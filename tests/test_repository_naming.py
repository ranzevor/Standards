import unittest
from checks.repository_naming import validate_name as check_name
def validate_name(name,**kwargs):
 return check_name(name,style="kebab-case",**kwargs)
class RepositoryNaming(unittest.TestCase):
 def test_default_and_brand_slugs(self):
  for name in ['standards','riversketch','image-workbench','3d-tools']:self.assertTrue(validate_name(name))
  self.assertTrue(validate_name('riversketch',brand_slug='riversketch'))
  self.assertFalse(validate_name('river-sketch',brand_slug='riversketch'))
 def test_bad_active_names(self):
  for name in ['Standards','hello_world','项目','hello--world','-hello','hello-','app-v2','app-20261023','app-2026-10-23','app-a101','app-new','app-final','app-copy','app-archive','app-repo','app-test']:
   with self.subTest(name=name):self.assertFalse(validate_name(name))
 def test_purpose_suffix_requires_role_and_reason(self):
  self.assertTrue(validate_name('atlas-sdk',role='sdk',suffix_reason='separate consumer SDK package'))
  self.assertTrue(validate_name('atlas-cli',role='cli',brand_slug='atlas',suffix_reason='separate installable command line interface'))
  self.assertTrue(validate_name('atlas-mcp',role='mcp-server',suffix_reason='MCP server boundary'))
  self.assertTrue(validate_name('atlas-monorepo',role='monorepo',suffix_reason='distinguish ecosystem workspace'))
  self.assertFalse(validate_name('atlas-sdk'));self.assertFalse(validate_name('atlas-cli',role='sdk',suffix_reason='wrong role'))
 def test_platform_exceptions_exact(self):
  self.assertTrue(validate_name('.github',kind='organization-profile'))
  self.assertTrue(validate_name('.github-private',kind='organization-profile'))
  self.assertTrue(validate_name('sample-user',kind='account-profile',account='sample-user'))
  self.assertTrue(validate_name('sample-user.github.io',kind='pages',account='sample-user'))
  self.assertTrue(validate_name('Upstream_Name',kind='upstream-fork',upstream='Upstream_Name'))
  self.assertFalse(validate_name('wrong.github.io',kind='pages',account='sample-user'))
  self.assertFalse(validate_name('fork-copy',kind='upstream-fork',upstream='Upstream_Name'))
 def test_archive_separate_policy(self):
  self.assertTrue(validate_name('sample-archive-2000-01-01',kind='archive'))
  self.assertFalse(validate_name('sample-archive-2000-02-30',kind='archive'))
  self.assertFalse(validate_name('sample-archive-2000-01-01'))
 def test_unknown_modes_fail_closed(self):
  self.assertFalse(validate_name('Valid_Name',kind='exception'))
  self.assertFalse(validate_name(None))

class NamingStyleDecision(unittest.TestCase):
 def test_selected_default(self):
  self.assertTrue(check_name('Standards'))
  self.assertFalse(check_name('standards'))
 def test_three_candidate_styles(self):
  self.assertTrue(check_name('image-workbench',style='kebab-case'))
  self.assertTrue(check_name('imageWorkbench',style='camelCase'))
  self.assertTrue(check_name('ImageWorkbench',style='PascalCase'))
  self.assertFalse(check_name('image-workbench',style='camelCase'))
  self.assertFalse(check_name('ImageWorkbench',style='kebab-case'))
 def test_brand_is_not_automatically_renamed(self):
  self.assertTrue(check_name('RiverSketch',style='PascalCase',brand_slug='RiverSketch'))
  self.assertFalse(check_name('RiverSketch',style='PascalCase',brand_slug='Riversketch'))

class SelectedNamingPolicy(unittest.TestCase):
 def test_acronyms_and_formal_brand(self):
  self.assertTrue(check_name('AtlasSDK',role='sdk',suffix_reason='separate SDK'))
  self.assertFalse(check_name('AtlasSdk',role='sdk',suffix_reason='separate SDK'))
  self.assertFalse(check_name('McpServer'))
  self.assertTrue(check_name('MCPServer'))
  self.assertTrue(check_name('iPhone',brand_slug='iPhone',brand_basis='synthetic-confirmed-brand-record'))
 def test_selected_no_versions_or_status(self):
  for name in ['StandardsV2','Standards20261023','StandardsA101','StandardsTemp','StandardsFinal']:
   self.assertFalse(check_name(name))

class BrandExceptions(unittest.TestCase):
 def test_confirmed_formal_brand_is_not_renamed_for_status_word(self):
  self.assertTrue(check_name('NewRelic',brand_slug='NewRelic',brand_basis='synthetic-confirmed-brand-record'))
  self.assertTrue(check_name('FinalDraft',brand_slug='FinalDraft',brand_basis='synthetic-confirmed-brand-record'))
  self.assertFalse(check_name('NewRelic',brand_slug='NewRelic'))

class HistoricalArchive(unittest.TestCase):
 def test_existing_archive_identity_not_retroactively_renamed(self):
  name='sample-archive-2000-01-01'
  self.assertTrue(validate_name(name,kind='historical-archive',historical_name=name,historical_basis='synthetic recorded archive identity'))
  self.assertFalse(validate_name(name,kind='historical-archive',historical_name='other',historical_basis='synthetic identity'))
  self.assertFalse(validate_name(name,kind='historical-archive',historical_name=name))
