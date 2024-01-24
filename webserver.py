from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from model import db, app,Edge

@app.route('/')
def index():
    edges = Edge.query.all()
    return render_template('index.html', edges=edges)


@app.route('/add_data', methods=['POST'])
def add_data():
    if request.method == 'POST':
        data = request.get_json()
        new_data = data.get('data')
        device_id = data.get('device_id')
        timestamp_str = data.get('timestamp')  # Get timestamp as a string

        if not new_data or not device_id or not timestamp_str:
            return jsonify({'error': 'Missing data, device_id, or timestamp in the request'}), 400

        # Convert timestamp string to a datetime object
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return jsonify({'error': 'Invalid timestamp format'}), 400

        existing_edge = Edge.query.filter_by(data=new_data, device_id=device_id).first()
        if existing_edge:
            return jsonify({'error': 'Data with the same device_id already exists'}), 400

        print("Timestamp:", timestamp)
        print("Edge Name:", device_id)
        print("Data:", new_data)
        new_edge = Edge(data=new_data, device_id=device_id, created_at=timestamp)
        db.session.add(new_edge)
        db.session.commit()

        return jsonify({'message': 'Data added successfully'}), 201

@app.route('/get_all_data', methods=['GET'])
def get_all_data():
    if request.method == 'GET':
        edges = Edge.query.all()
        edge_list = [{'id': edge.id, 'data': edge.data, 'device_id': edge.device_id, 'created_at': edge.created_at} for edge in edges]
        return jsonify({'data': edge_list})

# Define the route to get a single record by ID
@app.route('/get_data/<int:record_id>', methods=['GET'])
def get_data(record_id):
    if request.method == 'GET':
        edge = Edge.query.get(record_id)

        if edge:
            return jsonify({'id': edge.id, 'data': edge.data, 'device_id': edge.device_id, 'created_at': edge.created_at})
        else:
            return jsonify({'message': 'Record not found'}), 404



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='172.20.10.2', port=5000)
