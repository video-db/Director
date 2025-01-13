import asyncio


def is_event_loop_running():
    try:
        loop = asyncio.get_running_loop()
        print("EVENT LOOP CHECK : Event loop is running", loop)
        return True
    except RuntimeError as e:
        print("EVENT LOOP CHECK : Event loop is not running", e)
        return False
