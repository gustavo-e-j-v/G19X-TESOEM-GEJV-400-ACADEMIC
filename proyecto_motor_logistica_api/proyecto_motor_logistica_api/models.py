from sqlalchemy import Column, String, Integer, Boolean, Date, ForeignKey
from database import Base

class UbicacionRack(Base):
    __tablename__ = "ubicaciones_racks"

    id = Column(String, primary_key=True, index=True)
    nombre_producto = Column(String, nullable=True)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)
    ocupado = Column(Boolean, default=False)  # True = lleno, False = vacío/disponible


class HistorialPicking(Base):
    """Registra cuántas unidades se recogieron de un rack en un día dado.
    Es la materia prima para la clasificación ABC y la predicción de demanda."""
    __tablename__ = "historial_picking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rack_id = Column(String, ForeignKey("ubicaciones_racks.id"), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    cantidad_recogida = Column(Integer, nullable=False, default=0)


class Paquete(Base):
    """Paquete almacenado en un rack, con su fecha de entrega.
    Los datos los captura la persona desde la ventana emergente del rack."""
    __tablename__ = "paquetes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String, nullable=False, unique=True, index=True)
    descripcion = Column(String, nullable=True)
    rack_id = Column(String, ForeignKey("ubicaciones_racks.id"), nullable=False, index=True)
    fecha_entrega = Column(Date, nullable=False, index=True)
