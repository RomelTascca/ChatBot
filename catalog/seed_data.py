"""Datos de ejemplo (ficticios) para que la webapp funcione desde el primer minuto."""
from decimal import Decimal as D


def _img(text: str, color: str) -> str:
    return f"https://placehold.co/600x400/{color}/ffffff?text={text.replace(' ', '+')}"


CATEGORIES = ["Calzado", "Ropa", "Tecnología", "Accesorios"]

PRODUCTS = [
    dict(sku="CAL-001", name="Zapatillas Running AirFlex", category="Calzado", price=D("249.90"), old_price=D("299.90"),
         stock=35, sizes="38, 39, 40, 41, 42, 43, 44", emoji="👟", is_featured=True,
         description="Zapatillas livianas para running con amortiguación de espuma EVA, suela antideslizante y malla transpirable. Ideales para asfalto y pista."),
    dict(sku="CAL-002", name="Zapatillas Urbanas Lima Classic", category="Calzado", price=D("189.00"),
         stock=28, sizes="37, 38, 39, 40, 41, 42, 43", emoji="👟",
         description="Zapatillas de estilo casual en cuero sintético con plantilla acolchada. Combinan con jeans y ropa de oficina informal."),
    dict(sku="ROP-001", name="Polo Algodón Pima Básico", category="Ropa", price=D("59.90"),
         stock=120, sizes="S, M, L, XL", emoji="👕", is_featured=True,
         description="Polo manga corta 100% algodón pima peruano, cuello reforzado y tacto suave. Disponible en negro, blanco, azul marino y gris."),
    dict(sku="ROP-002", name="Casaca Rompevientos Andes", category="Ropa", price=D("229.00"),
         stock=0, sizes="S, M, L, XL", emoji="🧥",
         description="Casaca impermeable y ligera con capucha ajustable y bolsillos con cierre. Perfecta para viajes y días de lluvia ligera. Agotada temporalmente."),
    dict(sku="ROP-003", name="Jean Slim Fit Stretch", category="Ropa", price=D("129.90"), old_price=D("159.90"),
         stock=3, sizes="28, 30, 32, 34, 36", emoji="👖",
         description="Jean de corte slim con tela elástica para mayor comodidad. Lavado azul medio y cinco bolsillos clásicos. Quedan pocas unidades."),
    dict(sku="ACC-001", name="Mochila Urbana Antirrobo 20L", category="Accesorios", price=D("149.00"),
         stock=50, sizes="Talla única", emoji="🎒", is_featured=True,
         description="Mochila de 20 litros con compartimento acolchado para laptop de hasta 15.6\", cierres ocultos antirrobo y puerto de carga USB externo."),
    dict(sku="TEC-001", name="Audífonos Bluetooth NoiseOff Pro", category="Tecnología", price=D("299.00"), old_price=D("349.00"),
         stock=25, sizes="", emoji="🎧", is_featured=True,
         description="Audífonos premium con cancelación activa de ruido, Bluetooth 5.3, hasta 40 horas de batería y micrófono para llamadas. Garantía de 6 meses."),
    dict(sku="TEC-002", name="Smartwatch FitBand 5", category="Tecnología", price=D("219.00"),
         stock=40, sizes="", emoji="⌚",
         description="Reloj inteligente con monitor de ritmo cardíaco, conteo de pasos, notificaciones del celular y resistencia al agua 5 ATM. Batería de hasta 7 días."),
    dict(sku="TEC-003", name="Parlante Bluetooth Resistente al Agua", category="Tecnología", price=D("169.00"),
         stock=30, sizes="", emoji="🔊",
         description="Parlante portátil IPX7 con 12 horas de reproducción, sonido estéreo de 20 W y conexión para emparejar dos equipos."),
    dict(sku="TEC-004", name="Power Bank 20,000 mAh USB-C", category="Tecnología", price=D("119.00"),
         stock=60, sizes="", emoji="🔋",
         description="Batería externa de 20,000 mAh con carga rápida de 22.5 W, dos salidas USB y una USB-C. Incluye cable USB-C y estuche."),
    dict(sku="ACC-002", name="Gorra Trucker Bordada", category="Accesorios", price=D("39.90"),
         stock=85, sizes="Ajustable", emoji="🧢",
         description="Gorra estilo trucker con malla trasera transpirable y logo bordado. Cierre ajustable que se adapta a todas las tallas."),
    dict(sku="ACC-003", name="Botella Térmica Acero 750 ml", category="Accesorios", price=D("69.90"),
         stock=70, sizes="750 ml", emoji="🧴",
         description="Botella de acero inoxidable con doble pared: mantiene el frío 24 horas y el calor 12 horas. Tapa a prueba de fugas."),
]

for _p in PRODUCTS:
    _p["image_url"] = _img(_p["name"], "1e3a5f")

OFFERINGS = [
    dict(name="Delivery Lima Express", kind="servicio", icon="🛵", order=1,
         highlight="Mismo día si compras antes de las 2:00 p.m.",
         description="Entrega en Lima Metropolitana el mismo día para pedidos confirmados antes de las 2:00 p.m. Costo S/ 12; gratis en compras desde S/ 199."),
    dict(name="Envíos a provincias", kind="servicio", icon="📦", order=2,
         highlight="Olva Courier y Shalom · 2 a 5 días hábiles",
         description="Enviamos a todo el Perú por agencia. El costo depende del destino y se confirma antes de pagar. Recibes tu código de seguimiento por WhatsApp."),
    dict(name="Envío gratis desde S/ 199", kind="promocion", icon="🎁", order=3,
         highlight="Aplica a delivery en Lima",
         description="En compras desde S/ 199 el delivery en Lima Metropolitana es gratuito. En provincias se aplica un descuento sobre el costo de envío."),
    dict(name="Cambios y devoluciones en 7 días", kind="beneficio", icon="🔄", order=4,
         highlight="Con boleta y producto sin uso",
         description="Aceptamos cambios dentro de los 7 días posteriores a la entrega, con boleta, empaque original y producto sin uso. Si llegó con falla de fábrica, lo revisamos y te damos solución."),
    dict(name="Cambio de talla gratis", kind="beneficio", icon="📏", order=5,
         highlight="Un cambio sin costo de envío",
         description="Si la talla no te queda, hacemos un cambio de talla gratis por pedido, sujeto a stock, dentro del plazo de 7 días."),
    dict(name="Garantía en tecnología", kind="beneficio", icon="🛡️", order=6,
         highlight="6 meses por defectos de fábrica",
         description="Todos los productos de la categoría Tecnología incluyen 6 meses de garantía por defectos de fábrica. Atención de garantía por WhatsApp."),
    dict(name="Pago contra entrega (Lima)", kind="servicio", icon="💵", order=7,
         highlight="Paga al recibir tu pedido",
         description="Para pedidos con delivery en Lima puedes pagar en efectivo al recibir. Coordina el monto exacto por WhatsApp para facilitar el vuelto."),
    dict(name="Yape, Plin, tarjetas y transferencia", kind="servicio", icon="💳", order=8,
         highlight="Sin comisión adicional",
         description="Aceptamos Yape, Plin, tarjetas de crédito y débito, y transferencia bancaria. Te enviamos el comprobante electrónico por correo o WhatsApp."),
    dict(name="Atención por WhatsApp", kind="servicio", icon="💬", order=9,
         highlight="Lunes a sábado, 9:00 a.m. a 6:00 p.m.",
         description="Asesores humanos para coordinar pedidos, entregas, cambios y garantías. Fuera de horario puedes dejar tu mensaje y respondemos al siguiente día hábil."),
    dict(name="Compras por mayor", kind="plan", icon="🏷️", order=10,
         highlight="Precio especial desde 10 unidades",
         description="Plan para emprendedores y empresas: precio por mayor desde 10 unidades del mismo modelo, con factura y coordinación de entrega dedicada."),
    dict(name="Club Andina Puntos", kind="plan", icon="⭐", order=11,
         highlight="5% de tu compra en puntos",
         description="Acumula puntos en cada compra y canjéalos por descuentos en tu siguiente pedido. Registro gratuito con tu número de celular."),
    dict(name="Seguimiento de pedido", kind="funcionalidad", icon="📍", order=12,
         highlight="Estado y código de tracking en línea",
         description="Consulta el estado de tu pedido con tu número de orden y recibe avisos cuando sea despachado y cuando esté en camino."),
    dict(name="Asistente virtual con IA", kind="funcionalidad", icon="🤖", order=13,
         highlight="Disponible 24/7",
         description="Este chatbot responde sobre productos, precios, stock, envíos y devoluciones a cualquier hora. Si necesitas algo más, te deriva a un asesor humano."),
]
