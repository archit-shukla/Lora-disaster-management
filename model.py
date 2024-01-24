from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)


    
class Edge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(80), unique=False, nullable=False)
    device_id = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Edge {self.data} - Device ID: {self.device_id}>'
