import os
import sys
from pathlib import Path

# Set environment
os.environ['FLASK_ENV'] = 'production'

# Add project to path
sys.path.insert(0, str(Path.cwd()))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Fix database URL
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    os.environ['DATABASE_URL'] = db_url.replace('postgres://', 'postgresql://', 1)

# Create app
from app import create_app
app = create_app('production')

if __name__ == '__main__':
    import socket
    
    # Get IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Try to get WiFi IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        wifi_ip = s.getsockname()[0]
        s.close()
    except:
        wifi_ip = local_ip
    
    print('\n' + '='*70)
    print('Smart HRMS - HTTPS Server')
    print('='*70)
    print(f'\n✅ Server will be accessible at:\n')
    print(f'   https://{wifi_ip}')
    print(f'\n📱 On other computers on same WiFi network:')
    print(f'   Open browser to: https://{wifi_ip}')
    print(f'\n⚠️  Accept the certificate warning (self-signed is normal)')
    print(f'\n' + '='*70 + '\n')
    
    # Run with SSL
    app.run(
        host='0.0.0.0',
        port=443,
        ssl_context=('C:/Smart_HRMS/certs/smart-hrms.crt', 'C:/Smart_HRMS/certs/smart-hrms.key'),
        debug=False,
        use_reloader=False,
        threaded=True
    )
