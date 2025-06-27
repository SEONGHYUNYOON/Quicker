from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/cid/verify', methods=['GET', 'POST'])
def verify_cid():
    if request.method == 'GET':
        return jsonify({
            "status": "success",
            "message": "CID API is running",
            "method": "GET",
            "test_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_token"
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        cid = data.get('cid', None)
        phone = data.get('phone', None)
        
        if cid == "testcid":
            return jsonify({
                "status": "success", 
                "token": "dummy_token"
            })
        else:
            return jsonify({
                "status": "fail",
                "message": "CID not registered"
            })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Keeper CID API",
        "version": "1.0.0"
    })

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "Keeper CID Authentication API",
        "endpoints": {
            "verify_cid": "/api/cid/verify (GET/POST)",
            "health": "/api/health (GET)"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True) 