from android_sms_gateway import client, domain
import time
from mswd.settings import (
    SMS_SENDER_SERVER_IP,
    SMS_SENDER_SERVER_PORT,
    SMS_SENDER_SERVER_PASSWORD,
    SMS_SENDER_USERNAME,
)

def send_sms(api_client, message):
    try:
        print("Sending SMS...")
        state = api_client.send(message)
        print(f"Initial state: {state.state.name}")        
        time.sleep(5)
        state = api_client.get_state(state.id)
        print(f"Updated state: {state.state.name}")
        
        return {"status": "success", "message": 'Client has been successfully notified.'}
    except Exception as e:
        return {"status": "error", "message": "There was an error while sending a notification to client, please check your SMS API server.", "error": str(e)}

def sms_send(ip, port, username, password, message):
    base_url = f"http://{ip}:{port}"
    try:
        with client.APIClient(username, password, base_url=base_url) as api_client:
            return send_sms(api_client, message)
    except Exception as e:
        return {"status": "error", "message": "API Gateway is not running, or incorrect credentials.", "error": str(e)}

def send_sms_api_interface(message, mobile):
    mobile = [mobile]
    message = domain.Message(message, mobile)
    return sms_send(
        SMS_SENDER_SERVER_IP,
        SMS_SENDER_SERVER_PORT,
        SMS_SENDER_USERNAME,
        SMS_SENDER_SERVER_PASSWORD,
        message,
    )