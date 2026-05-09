import sys
import traceback

try:
    print('Starting server...')
    from chat_proxy_server import run_server
    print('Import successful')
    run_server()
except Exception as e:
    print('Error:', type(e).__name__, str(e))
    traceback.print_exc()
    sys.exit(1)