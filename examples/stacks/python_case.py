"""Actual Python value and cooperative-cancellation fixture, no external effects."""
import asyncio

def quantity(value):
    if type(value) is not int or value < 0:
        raise ValueError('quantity')
    return value

def check(condition, message):
    if not condition:
        raise RuntimeError(message)

for value in [0, 7]:
    check(quantity(value)==value,'legal integer')
for value in [True, -1, 0.5, None]:
    try:quantity(value)
    except ValueError:pass
    else:raise RuntimeError('invalid quantity accepted')

async def main():
    started=asyncio.Event(); cleaned=[]
    async def operation():
        try:
            started.set()
            await asyncio.Event().wait()
        finally:
            cleaned.append('local-resource-released')
    task=asyncio.create_task(operation())
    await started.wait()
    task.cancel()
    try:await task
    except asyncio.CancelledError:pass
    else:raise RuntimeError('cancellation swallowed')
    check(cleaned==['local-resource-released'],'cleanup')
    check(task.cancelled(),'actual local task terminal state')
asyncio.run(main())
print('python-contract-ok')
