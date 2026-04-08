"""
models.py — Modelos SQLAlchemy (preparados para uso futuro)

STATUS: PREPARADO, NAO ATIVO
O sistema ainda usa JSON para persistencia.
Para ativar, siga os passos no final deste arquivo.

Quando ativar, os models abaixo substituem os arquivos JSON
sem mudar nenhuma interface do sistema.
"""

# -- DESCOMENTE QUANDO QUISER ATIVAR O BANCO ----------------------------------
#
# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime
#
# db = SQLAlchemy()
#
#
# class Cliente(db.Model):
#     """Representa um cliente cadastrado no sistema."""
#     __tablename__ = "clientes"
#
#     id         = db.Column(db.Integer, primary_key=True)
#     nome       = db.Column(db.String(200), nullable=False, unique=True)
#     criado_em  = db.Column(db.DateTime, default=datetime.utcnow)
#
#     rotas = db.relationship("Rota", backref="cliente_ref", lazy=True)
#
#     def to_dict(self):
#         return {"id": self.id, "nome": self.nome}
#
#
# class Rota(db.Model):
#     """Representa uma rota calculada e salva."""
#     __tablename__ = "rotas"
#
#     id            = db.Column(db.Integer, primary_key=True)
#     nome          = db.Column(db.String(200))
#     cliente_id    = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=True)
#     data          = db.Column(db.DateTime, default=datetime.utcnow)
#     distancia_km  = db.Column(db.Float)
#     duracao_min   = db.Column(db.Float)
#     custo         = db.Column(db.Float)
#     rota_json     = db.Column(db.Text)   # geometria serializada
#     instrucoes_json = db.Column(db.Text) # instrucoes serializadas
#
#     def to_dict(self):
#         import json
#         return {
#             "id":           self.id,
#             "nome":         self.nome,
#             "cliente":      self.cliente_ref.nome if self.cliente_ref else "Sem cliente",
#             "data":         self.data.isoformat(),
#             "distancia_km": self.distancia_km,
#             "duracao_min":  self.duracao_min,
#             "custo":        self.custo,
#             "rota":         json.loads(self.rota_json or "[]"),
#             "instrucoes":   json.loads(self.instrucoes_json or "[]"),
#         }
#
#
# -- PASSOS PARA ATIVAR O BANCO ------------------------------------------------
#
# 1. Descomente o codigo acima
# 2. No requirements.txt: certifique-se que Flask-SQLAlchemy esta instalado
# 3. No config.py: descomente a linha DATABASE_URL
# 4. No app.py: adicione:
#      from flask_sqlalchemy import SQLAlchemy
#      from database.models import db
#      app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
#      db.init_app(app)
#      with app.app_context():
#          db.create_all()
# 5. No storage_service.py: substitua as funcoes _ler_json/_escrever_json
#    por queries SQLAlchemy mantendo a mesma interface publica
