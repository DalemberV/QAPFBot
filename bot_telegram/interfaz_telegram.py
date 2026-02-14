import os
import logging
import modal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from cerebro import GeologoAI 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.environ.get("TELEGRAM_TOKEN", "TOKEN_LOCAL")

try:
    sessions = modal.Dict.from_name("geo-sessions", create_if_missing=True)
except:
    sessions = {} 

try:
    geo_bot = GeologoAI()
except Exception as e:
    geo_bot = None

def get_session(user_id):
    default = {'mode': None, 'step': None, 'textura': [], 'color': None, 'minerales': [], 'q': 0, 'a': 0, 'p': 0}
    return sessions.get(user_id, default) if isinstance(sessions, dict) else sessions.get(user_id, default)

def save_session(user_id, data):
    sessions[user_id] = data

# --- HELPER--
def get_mineral_keyboard():
    return [
        [InlineKeyboardButton("⚪ Cuarzo", callback_data='min_cuarzo'), InlineKeyboardButton("🌸 Feld. K", callback_data='min_feldespato_k')],
        [InlineKeyboardButton("⬜ Plagioclasa", callback_data='min_plagioclasa'), InlineKeyboardButton("⬛ Anfíbol/Biotita", callback_data='min_anfibol')],
        [InlineKeyboardButton("🟩 Piroxeno", callback_data='min_piroxeno'), InlineKeyboardButton("🫒 Olivino", callback_data='min_olivino')],
        [InlineKeyboardButton("✅ TERMINAR Y ANALIZAR", callback_data='DONE_VISUAL')]
    ]

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_session(user_id, {'mode': None, 'step': None, 'textura': [], 'color': None, 'minerales': [], 'q': 0, 'a': 0, 'p': 0})
    
    keyboard = [
        [InlineKeyboardButton("🔍 Modo Campo (Visual)", callback_data='mode_visual')],
        [InlineKeyboardButton("🧪 Modo Lab (QAPF)", callback_data='mode_qapf')]
    ]
    await update.message.reply_text("⚒️ **GeoExpert Bot**\nSelecciona método:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    session = get_session(user_id)

    # SELECCIÓN DE MODO
    if data == 'mode_visual':
        session['mode'] = 'visual'
        keyboard = [
            [InlineKeyboardButton("Fanerítica", callback_data='tex_faneritica')],
            [InlineKeyboardButton("Afanítica", callback_data='tex_afanitica')],
            [InlineKeyboardButton("Vítrea", callback_data='tex_vitrea')],
            [InlineKeyboardButton("Vesicular", callback_data='tex_vesicular')],
            [InlineKeyboardButton("Piroclástica", callback_data='tex_piroclastica')]
        ]
        await query.edit_message_text("🔍 **Modo Visual**\nTextura:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        save_session(user_id, session)

    elif data == 'mode_qapf':
        session['mode'] = 'qapf'
        keyboard = [[InlineKeyboardButton("Fanerítica (Intrusiva)", callback_data='qap_tex_faneritica')], [InlineKeyboardButton("Afanítica (Extrusiva)", callback_data='qap_tex_afanitica')]]
        await query.edit_message_text("🧪 **Modo QAPF**\nAmbiente:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        save_session(user_id, session)

    # LÓGICA VISUAL
    elif session.get('mode') == 'visual':
        if data.startswith("tex_"):
            val = data.replace("tex_", "")
            session['textura'] = [val]
            keyboard = [
                [InlineKeyboardButton("Leucocrático (Claro)", callback_data='col_leucocratico')],
                [InlineKeyboardButton("Mesocrático (Medio)", callback_data='col_mesocratico')],
                [InlineKeyboardButton("Melanocrático (Oscuro)", callback_data='col_melanocratico')],
                [InlineKeyboardButton("Ultramáfico (Verde/Negro)", callback_data='col_ultramafico')]
            ]
            await query.edit_message_text(f"Textura: {val}\n\nSelecciona Índice de Color:", reply_markup=InlineKeyboardMarkup(keyboard))
        
        elif data.startswith("col_"):
            val = data.replace("col_", "")
            session['color'] = val
            # AQUÍ USAMOS LA FUNCIÓN HELPER PARA MOSTRAR TODOS LOS MINERALES
            await query.edit_message_text(f"Color: {val}\n\nSelecciona los minerales presentes:", reply_markup=InlineKeyboardMarkup(get_mineral_keyboard()))
        
        elif data.startswith("min_"):
            val = data.replace("min_", "")
            if val not in session['minerales']:
                session['minerales'].append(val)
            # VOLVEMOS A MOSTRAR EL TECLADO COMPLETO
            await query.edit_message_text(f"Minerales: {', '.join(session['minerales'])}\n\n¿Hay otro mineral?", reply_markup=InlineKeyboardMarkup(get_mineral_keyboard()))

        elif data == "DONE_VISUAL":
             tex = session['textura'][0] if session['textura'] else 'desconocida'
             res = geo_bot.identificar_visual(tex, session['minerales'], session['color'])
             if res: await query.edit_message_text(f"✅ Resultado: **{res[0].upper()}**", parse_mode='Markdown')
             else: await query.edit_message_text("⚠️ No coincide con una clasificación estándar.\nRevisa incompatibilidades (ej. Olivino + Cuarzo).", parse_mode='Markdown')

        save_session(user_id, session)

    # LÓGICA QAPF
    elif data.startswith("qap_tex_"):
        val = data.replace("qap_tex_", "")
        session['textura'] = val
        session['step'] = 'WAITING_Q'
        await query.edit_message_text(f"Ambiente: **{val.upper()}**.\nEscribe % de **Cuarzo (Q)**:", parse_mode='Markdown')
        save_session(user_id, session)

# HANDLER TEXTO (QAPF)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    session = get_session(user_id)
    step = session.get('step')
    
    if not step or session.get('mode') != 'qapf': return

    try:
        valor = float(text)
        if not (0 <= valor <= 100): raise ValueError
    except:
        await update.message.reply_text("⚠️ Ingresa un número válido (0-100).")
        return

    if step == 'WAITING_Q':
        session['q'] = valor
        session['step'] = 'WAITING_A'
        await update.message.reply_text(f"Q={valor}%. Escribe % **Feld. Alcalino (A)**:")
    elif step == 'WAITING_A':
        session['a'] = valor
        session['step'] = 'WAITING_P'
        await update.message.reply_text(f"A={valor}%. Escribe % **Plagioclasa (P)**:")
    elif step == 'WAITING_P':
        session['p'] = valor
        total = session['q'] + session['a'] + valor
        if abs(total - 100) > 1.0:
            session['step'] = 'WAITING_Q'
            await update.message.reply_text(f"🛑 Suma {total}%. Debe ser 100%.\nReiniciando... Dime Q:")
        else:
            session['step'] = None
            res = geo_bot.identificar_qapf(session['textura'], session['q'], session['a'], session['p'])
            msg = f"🎉 Roca: **{res[0].upper()}**" if res else "⚠️ Indeterminado en QAPF."
            await update.message.reply_text(msg, parse_mode='Markdown')
    
    save_session(user_id, session)