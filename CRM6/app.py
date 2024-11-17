from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_pymongo import PyMongo
from datetime import datetime
from bson import ObjectId
import sys

app = Flask(__name__)

# Configuración de MongoDB
app.config["MONGO_URI"] = "mongodb+srv://carlossv3130:4VJd4yX8viAsDjqB@cluster0.w7fek.mongodb.net/crm_db?retryWrites=true&w=majority&appName=Cluster0"
mongo = PyMongo(app)

# Verificar conexión con MongoDB
try:
    mongo.cx.server_info()
    print("Conexión a MongoDB Atlas exitosa")
except Exception as e:
    print(f"Error de conexión a MongoDB Atlas: {e}", file=sys.stderr)

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# Registrar cliente
@app.route('/add_client', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        documento = request.form['documento']
        fecha_cita = request.form['fecha_cita']
        hora_cita = request.form['hora_cita']

        # Guardar cliente en MongoDB
        cliente = {
            "nombre": nombre,
            "email": email,
            "telefono": telefono,
            "documento": documento,
            "fecha_cita": datetime.strptime(f"{fecha_cita} {hora_cita}", "%Y-%m-%d %H:%M"),
            "interacciones": [],
            "contratos": []
        }
        mongo.db.clientes.insert_one(cliente)
        return redirect(url_for('index'))
    return render_template('add_client.html')

# Ver cliente
@app.route('/view_client/<client_id>')
def view_client(client_id):
    cliente = mongo.db.clientes.find_one_or_404({'_id': ObjectId(client_id)})
    return render_template('view_client.html', cliente=cliente)

# Ver todas las citas
@app.route('/citas')
def citas():
    citas = mongo.db.clientes.find({'fecha_cita': {'$ne': None}}).sort('fecha_cita', 1)
    return render_template('citas.html', citas=citas)

# Marcar cita como cumplida y eliminarla
@app.route('/citas/mark_completed/<cita_id>', methods=['POST'])
def mark_completed(cita_id):
    mongo.db.clientes.update_one(
        {"_id": ObjectId(cita_id)},
        {"$set": {"fecha_cita": None}}
    )
    return jsonify({"success": True})

# Agregar interacciones a cliente
@app.route('/add_interaction/<client_id>', methods=['POST'])
def add_interaction(client_id):
    descripcion = request.form['descripcion']
    interaccion = {
        "descripcion": descripcion,
        "fecha": datetime.utcnow()
    }
    mongo.db.clientes.update_one(
        {'_id': ObjectId(client_id)},
        {'$push': {'interacciones': interaccion}}
    )
    return redirect(url_for('view_client', client_id=client_id))

# Agregar contrato a cliente
@app.route('/add_contract/<client_id>', methods=['POST'])
def add_contract(client_id):
    descripcion = request.form['descripcion']
    contrato = {
        "descripcion": descripcion,
        "fecha_inicio": datetime.utcnow()
    }
    mongo.db.clientes.update_one(
        {'_id': ObjectId(client_id)},
        {'$push': {'contratos': contrato}}
    )
    return redirect(url_for('view_client', client_id=client_id))

# API de clientes
@app.route('/api/clients', methods=['GET'])
def get_clients():
    clientes = list(mongo.db.clientes.find())
    for cliente in clientes:
        cliente['_id'] = str(cliente['_id'])
        if cliente['fecha_cita']:
            cliente['fecha_cita'] = cliente['fecha_cita'].strftime('%Y-%m-%d %H:%M')
        else:
            cliente['fecha_cita'] = None
    return jsonify(clientes)

# API para obtener citas
@app.route('/api/citas', methods=['GET'])
def get_citas():
    citas = list(mongo.db.clientes.find({'fecha_cita': {'$ne': None}}).sort('fecha_cita', 1))
    for cita in citas:
        cita['_id'] = str(cita['_id'])
        cita['fecha_cita'] = cita['fecha_cita'].strftime('%Y-%m-%d %H:%M')
    return jsonify(citas)

# Generar reporte de clientes y contratos
@app.route('/reporte_clientes')
def reporte_clientes():
    clientes = list(mongo.db.clientes.find())
    report_data = []
    for cliente in clientes:
        contratos = cliente.get('contratos', [])
        report_data.append({
            "cliente": cliente.get("nombre", "N/A"),
            "documento": cliente.get("documento", "N/A"),
            "email": cliente.get("email", "N/A"),
            "telefono": cliente.get("telefono", "N/A"),
            "contratos": [{"descripcion": c["descripcion"], "fecha_inicio": c["fecha_inicio"].strftime('%Y-%m-%d')} for c in contratos],
            "total_contratos": len(contratos)
        })
    return render_template('reporte_clientes.html', report_data=report_data)

if __name__ == '__main__':
    app.run(debug=True, port=3000)
