"""Real local Chromium fixture tests; no IME, AT, cross-browser or production claim."""
import importlib.metadata,json,os,platform,tempfile,threading,unittest
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=[]
BROWSER_EXECUTABLE=os.environ.get("STANDARDS_BROWSER_EXECUTABLE","/usr/bin/chromium")
TARGET_ENABLED=os.environ.get("STANDARDS_RUN_BROWSER_TARGETS")=="1"
OUTPUT=Path(os.environ.get("STANDARDS_BROWSER_EVIDENCE_DIR",str(Path(tempfile.gettempdir())/"StandardsBrowserContracts")))/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/native'):
            body=('<!doctype html><title>Native submission</title><pre>'+self.path+'</pre>').encode()
        else:
            body=(ROOT/'examples/web-backend/browser_contracts.html').read_bytes()
        self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): pass

@unittest.skipUnless(TARGET_ENABLED,"real browser target is opt-in; no browser/IME/AT claim")
class BrowserContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base='http://127.0.0.1:'+str(cls.server.server_port)
        cls.pw=sync_playwright().start()
        try:
            cls.browser=cls.pw.chromium.launch(executable_path=BROWSER_EXECUTABLE,headless=True,chromium_sandbox=True)
            cls.version=cls.browser.version
        except Exception as exc:
            OUTPUT.mkdir(parents=True,exist_ok=False)
            (OUTPUT/'web-backend-browser-results.json').write_text(json.dumps({
                'date':datetime.now(timezone.utc).isoformat(),'status':'blocked','tests_executed':0,'runtime_status':'not-run',
                'executable':BROWSER_EXECUTABLE,'sandbox_enabled':True,'error':str(exc),
                'scope':'synthetic loopback fixture; no IME/AT/cross-browser result'},ensure_ascii=False,indent=2)+'\n')
            cls.pw.stop();cls.server.shutdown();cls.server.server_close();cls.thread.join()
            raise
    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.server.server_close();cls.thread.join()
        out=OUTPUT/'web-backend-browser-results.json'
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps({'date':datetime.now(timezone.utc).isoformat(),'browser':'Chromium','browser_version':cls.version,
          'executable':BROWSER_EXECUTABLE,'sandbox_enabled':True,'headless':True,'os':platform.platform(),
          'playwright_python':importlib.metadata.version('playwright'),'origin':'loopback HTTP, synthetic fixture',
          'scope':'native controls, History and deterministic Promise landing order only; not real system IME/AT/Safari/PWA',
          'observations':EVIDENCE},ensure_ascii=False,indent=2)+'\n')
    def setUp(self):
        self.context=self.browser.new_context();self.page=self.context.new_page();self.page.goto(self.base+'/')
        type(self).version=self.browser.version
    def tearDown(self):
        if not self.page.is_closed():
            EVIDENCE.append({'test':self._testMethodName,'url':self.page.url,'events':self.page.evaluate('window.events??[]'),
              'view':self.page.locator('#view').evaluate('(e)=>e.value') if self.page.locator('#view').count() else None})
        self.context.close()
    def test_native_required_blocks_invalid_then_preserves_submitter_and_successful_controls(self):
        self.page.get_by_role('button',name='发布',exact=True).click()
        self.assertEqual(self.page.evaluate('events.filter(x=>x.type==="submit").length'),0)
        self.assertEqual(self.page.evaluate('events.filter(x=>x.type==="invalid").map(x=>x.field)'),['title'])
        self.page.get_by_label('标题',exact=True).fill('alpha')
        self.page.get_by_role('button',name='发布',exact=True).click()
        event=self.page.evaluate('events.find(x=>x.type==="submit")')
        self.assertEqual(event['submitter'],'publish');self.assertEqual(event['entries'],[['title','alpha'],['readonly','kept'],['intent','publish']])
        self.assertTrue(event['trusted'])
    def test_keyboard_enter_uses_native_default_submitter_without_composition_claim(self):
        self.page.get_by_label('标题',exact=True).fill('keyboard')
        self.page.get_by_label('标题',exact=True).press('Enter')
        event=self.page.evaluate('events.find(x=>x.type==="submit")')
        self.assertEqual(event['submitter'],'save');self.assertEqual(event['entries'][-1],['intent','save'])
    def test_request_submit_validates_and_direct_submit_mutation_bypasses_validation_event(self):
        self.page.evaluate('edit.requestSubmit(document.getElementById("publish"))')
        self.assertEqual(self.page.evaluate('events.filter(x=>x.type==="submit").length'),0)
        self.assertEqual(self.page.evaluate('events.filter(x=>x.type==="invalid").length'),1)
        self.page.evaluate('edit.submit()')
        self.page.wait_for_url('**/native?*')
        self.assertIn('title=&readonly=kept',self.page.url)
        self.assertNotIn('intent=',self.page.url)
        EVIDENCE.append({'test':self._testMethodName,'mutation':'form.submit bypassed required/submit listener and navigated with blank title','observed_url':self.page.url})
    def test_disabled_before_formdata_mutation_loses_value_but_readonly_is_legal(self):
        self.page.get_by_label('标题',exact=True).fill('preserve')
        safe=self.page.evaluate('[...new FormData(edit,document.getElementById("save"))]')
        broken=self.page.evaluate('document.getElementById("title").disabled=true;[...new FormData(edit,document.getElementById("save"))]')
        self.assertIn(['title','preserve'],safe);self.assertNotIn(['title','preserve'],broken)
        self.assertIn(['readonly','kept'],safe);self.assertIn(['readonly','kept'],broken)
        EVIDENCE.append({'test':self._testMethodName,'safe_entries':safe,'mutation_entries':broken,'failure_oracle':'title must not disappear from the intended snapshot'})
    def test_propagation_and_default_are_independent(self):
        self.page.locator('#link').click();self.page.wait_for_url('**/#destination')
        self.assertEqual(self.page.evaluate('events.filter(x=>x.type==="outer-click").length'),0)
        self.page.evaluate('history.replaceState(null,"","/");events=[];eventMode="prevent"')
        self.page.locator('#link').click()
        self.assertEqual(self.page.url,self.base+'/')
        self.assertEqual(self.page.evaluate('events.filter(x=>x.type==="outer-click").length'),1)
    def test_native_modal_escape_restores_opener_focus(self):
        self.page.get_by_role('button',name='打开对话框').click()
        self.assertEqual(self.page.evaluate('document.activeElement.id'),'draft')
        self.page.keyboard.press('Escape')
        self.assertFalse(self.page.locator('#dialog').evaluate('(e)=>e.open'))
        self.assertEqual(self.page.evaluate('document.activeElement.id'),'open')
    def test_push_state_does_not_emit_popstate_back_forward_do(self):
        self.page.locator('#route-a').click();self.page.locator('#route-b').click()
        self.assertEqual(self.page.evaluate('events.filter(x=>x.type==="popstate").length'),0)
        self.page.go_back();self.assertTrue(self.page.url.endswith('/route/a'))
        self.page.wait_for_function('events.filter(x=>x.type==="popstate").length===1')
        self.page.go_forward();self.assertTrue(self.page.url.endswith('/route/b'))
        self.page.wait_for_function('events.filter(x=>x.type==="popstate").length===2')
        self.assertEqual(self.page.evaluate('events.filter(x=>x.type==="popstate").map(x=>x.state.route)'),['a','b'])
    def start(self,label,guard=True):
        self.page.evaluate('([label,guard])=>{begin(label,{guard});return null}',[label,guard])
    def finish(self,label,value):
        self.page.evaluate('([label,value])=>complete(label,value)',[label,value])
        self.page.wait_for_function('(label)=>events.some(x=>x.type==="landing"&&x.label===label)',arg=label)
    def test_old_account_callback_rejected_current_identity_neighbor_accepted(self):
        self.start('A');self.page.locator('#switch').click();self.finish('A','A-secret')
        self.assertEqual(self.page.locator('#view').evaluate('(e)=>e.value'),'B-empty')
        self.start('B');self.finish('B','B-result')
        self.assertEqual(self.page.locator('#view').evaluate('(e)=>e.value'),'B-result')
        self.assertEqual(self.page.evaluate('events.filter(x=>x.type==="landing").map(x=>x.accepted)'),[False,True])
    def test_missing_identity_guard_mutation_exposes_old_account(self):
        self.start('broken',False);self.page.locator('#switch').click();self.finish('broken','A-secret')
        self.assertEqual(self.page.locator('#view').evaluate('(e)=>e.value'),'A-secret')
        EVIDENCE.append({'test':self._testMethodName,'mutation_failure_observed':'A content became visible after switching to B'})
    def test_reversed_query_completion_keeps_latest_and_legal_current_completion(self):
        self.start('old');self.start('current');self.finish('current','new');self.finish('old','old')
        self.assertEqual(self.page.locator('#view').evaluate('(e)=>e.value'),'new')
        self.assertEqual(self.page.evaluate('events.filter(x=>x.type==="landing").map(x=>x.accepted)'),[True,False])

if __name__=='__main__':unittest.main(verbosity=2)
