// ==========================================
// md2kindle Telegram Bot - Google Apps Script
// ==========================================
// Este script corre cada 30 segundos via trigger
// Gestiona comandos entrantes y dispara GitHub Actions
// ==========================================

// ---- CONFIGURACIÓN (Propiedades del script) ----
const getScriptProperties = () => {
  const props = PropertiesService.getScriptProperties();
  return {
    TELEGRAM_TOKEN: props.getProperty('TELEGRAM_TOKEN'),
    TELEGRAM_CHAT_ID: props.getProperty('TELEGRAM_CHAT_ID'),
    GITHUB_TOKEN: props.getProperty('GITHUB_TOKEN'),
    GITHUB_REPO: props.getProperty('GITHUB_REPO'),
    GITHUB_WORKFLOW_ID: props.getProperty('GITHUB_WORKFLOW_ID')
  };
};

// ---- ESTADO DE LA CONVERSACIÓN ----
// Estructura para guardar el estado de cada usuario
// conversationStates: { chatId: { step: 'waiting_mode', url: '...', mode: 'v', start: null, end: null, lang: 'es-la', skipOneshots: true } }
let conversationStates = {};
let lastUpdateId = 0;

// ---- FUNCIONES AUXILIARES ----

function sendTelegramMessage(text) {
  const props = getScriptProperties();
  const url = `https://api.telegram.org/bot${props.TELEGRAM_TOKEN}/sendMessage`;
  const data = {
    chat_id: props.TELEGRAM_CHAT_ID,
    text: text,
    parse_mode: 'Markdown'
  };
  UrlFetchApp.fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    payload: JSON.stringify(data)
  });
}

function sendTelegramReply(chatId, text) {
  const props = getScriptProperties();
  const url = `https://api.telegram.org/bot${props.TELEGRAM_TOKEN}/sendMessage`;
  const data = {
    chat_id: chatId,
    text: text,
    parse_mode: 'Markdown'
  };
  UrlFetchApp.fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    payload: JSON.stringify(data)
  });
}

function getTelegramUpdates() {
  const props = getScriptProperties();
  const url = `https://api.telegram.org/bot${props.TELEGRAM_TOKEN}/getUpdates?offset=${lastUpdateId + 1}&timeout=1`;
  try {
    const response = UrlFetchApp.fetch(url, { method: 'GET' });
    return JSON.parse(response.getContentText());
  } catch (e) {
    return null;
  }
}

function validateMangaDexUrl(url) {
  const match = url.match(/(title|manga|chapter)\/([a-f0-9-]{36}|[0-9]+)/i);
  if (!match) return { valid: false, error: 'URL no válida. Formato esperado: https://mangadex.org/title/UUID' };

  const linkType = match[1].toLowerCase();
  const uuid = match[2];

  // Si es chapter, obtener el manga UUID primero
  if (linkType === 'chapter') {
    try {
      const apiUrl = `https://api.mangadex.org/chapter/${uuid}?includes[]=manga`;
      const response = UrlFetchApp.fetch(apiUrl, { method: 'GET' });
      const data = JSON.parse(response.getContentText());
      if (data.result === 'ok' && data.data) {
        const relationships = data.data.relationships || [];
        for (const rel of relationships) {
          if (rel.type === 'manga') {
            return { valid: true, uuid: rel.id, type: 'chapter', chapterNum: data.data.attributes?.chapter };
          }
        }
      }
    } catch (e) {
      return { valid: false, error: 'No se pudo validar la URL en MangaDex' };
    }
  }

  return { valid: true, uuid: uuid, type: linkType };
}

function triggerGitHubWorkflow(params) {
  const props = getScriptProperties();
  const [owner, repo] = props.GITHUB_REPO.split('/');

  const url = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${props.GITHUB_WORKFLOW_ID}/dispatches`;

  const payload = {
    ref: 'main',
    inputs: {
      url: { value: params.url },
      mode: { value: params.mode },
      start: { value: params.start },
      end: { value: params.end },
      lang: { value: params.lang },
      skip_oneshots: { value: params.skipOneshots }
    }
  };

  const options = {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${props.GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3+json',
      'Content-Type': 'application/json'
    },
    payload: JSON.stringify(payload)
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    return response.getResponseCode() === 204;
  } catch (e) {
    return false;
  }
}

// ---- MANEJO DE COMANDOS ----

function handleStart(chatId) {
  const helpText = `🤖 *md2kindle Bot*\n\n`
    + `Comandos disponibles:\n\n`
    + `/descargar <url> - Iniciar descarga interactiva\n`
    + `/help - Mostrar esta ayuda\n`
    + `/status - Ver estado del bot\n`
    + `/list - Ver últimas descargas\n`
    + `/cancel - Cancelar una descarga en progreso\n\n`
    + `Ejemplo: /descargar https://mangadex.org/title/abc-123`;
  sendTelegramReply(chatId, helpText);
}

function handleHelp(chatId) {
  handleStart(chatId);
}

function handleStatus(chatId) {
  const props = getScriptProperties();
  const statusText = `✅ *Estado del Bot*\n\n`
    + `Token: ${props.TELEGRAM_TOKEN ? '✅ Configurado' : '❌ Falta'}\n`
    + `Chat ID: ${props.TELEGRAM_CHAT_ID ? '✅ Configurado' : '❌ Falta'}\n`
    + `GitHub Repo: ${props.GITHUB_REPO || '❌ Falta'}\n`
    + `Workflow: ${props.GITHUB_WORKFLOW_ID || '❌ Falta'}\n\n`
    + `Intervalo de polling: 30 segundos`;
  sendTelegramReply(chatId, statusText);
}

function handleList(chatId) {
  const history = getHistory();
  if (history.length === 0) {
    sendTelegramReply(chatId, '📭 No hay descargas recientes.');
    return;
  }

  let text = '📚 *Últimas descargas:*\n\n';
  history.slice(-5).reverse().forEach((item, i) => {
    text += `${i + 1}. ${item.title} (${item.mode} ${item.start}-${item.end})\n`;
    text += `   📅 ${item.date}\n\n`;
  });
  sendTelegramReply(chatId, text);
}

function handleCancel(chatId, params) {
  sendTelegramReply(chatId, '⚠️ La cancelación de workflows no está soportada directamente. '
    + 'Podés esperar a que termine o cancelar desde la interfaz de GitHub Actions.');
}

function handleDownload(chatId, url) {
  if (!url) {
    sendTelegramReply(chatId, '❌ Formato incorrecto.\nUso: /descargar <url_mangadex>\n\n'
      + 'Ejemplo: /descargar https://mangadex.org/title/abc-123');
    return;
  }

  // Validar URL
  const validation = validateMangaDexUrl(url);
  if (!validation.valid) {
    sendTelegramReply(chatId, `❌ ${validation.error}`);
    return;
  }

  // Guardar estado inicial de la conversación
  conversationStates[chatId] = {
    step: 'waiting_mode',
    url: url,
    mangaUuid: validation.uuid,
    mode: null,
    start: null,
    end: null,
    lang: 'es-la',
    skipOneshots: true
  };

  sendTelegramReply(chatId, `✅ URL válida: ${validation.uuid}\n\n`
    + `📖 Configurando descarga...\n\n`
    + `_Iniciando proceso interactivo..._\n\n`
    + `*Paso 1/5*\n`
    + `¿Modo?\n`
    + `  (v)olumen - Descarga tomos completos\n`
    + `  (c)apítulo - Descarga capítulos individuales\n\n`
    + `Responde: v o c`);
}

function handleInteractiveResponse(chatId, text) {
  const state = conversationStates[chatId];
  if (!state) {
    sendTelegramReply(chatId, '🔄 Sesión expirada. Usa /descargar <url> para iniciar.');
    return;
  }

  const response = text.trim().toLowerCase();

  switch (state.step) {
    case 'waiting_mode':
      if (response === 'v' || response === 'volumen') {
        state.mode = 'v';
        state.step = 'waiting_start';
        sendTelegramReply(chatId, '✅ Modo: Volumen\n\n'
          + '*Paso 2/5*\n'
          + '¿Número inicial del volumen?\n\n'
          + 'Ejemplo: 1, 5, 10, S1');
      } else if (response === 'c' || response === 'capitulo') {
        state.mode = 'c';
        state.step = 'waiting_start';
        sendTelegramReply(chatId, '✅ Modo: Capítulo\n\n'
          + '*Paso 2/5*\n'
          + '¿Número inicial del capítulo?\n\n'
          + 'Ejemplo: 1, 50, 100.5');
      } else {
        sendTelegramReply(chatId, '❌ Respuesta no válida. Responde: v (volumen) o c (capítulo)');
      }
      break;

    case 'waiting_start':
      const startNum = parseFloat(response);
      if (isNaN(startNum) || startNum <= 0) {
        sendTelegramReply(chatId, '❌ Número no válido. Ingresa un número positivo.\n'
          + 'Ejemplo: 1, 5, 10');
        return;
      }
      state.start = response;
      state.step = 'waiting_end';
      const promptEnd = state.mode === 'v' ? 'volumen' : 'capítulo';
      sendTelegramReply(chatId, `✅ Volumen inicial: ${state.start}\n\n`
        + `*Paso 3/5*\n`
        + `¿Número final del ${promptEnd}?\n\n`
        + `Ejemplo: 5, 10 (o Enter para solo el ${state.start})`);
      break;

    case 'waiting_end':
      const endNum = parseFloat(response);
      if (response === '' || response === state.start) {
        state.end = state.start;
        state.step = 'waiting_lang';
        askLanguage(chatId, state);
      } else if (isNaN(endNum) || endNum <= 0) {
        sendTelegramReply(chatId, `❌ Número no válido. Ingresa un número positivo o Enter para ${state.start}`);
        return;
      } else {
        state.end = response;
        state.step = 'waiting_lang';
        askLanguage(chatId, state);
      }
      break;

    case 'waiting_lang':
      const langMap = { 'es-la': 'es-la', 'es': 'es', 'en': 'en' };
      if (langMap[response]) {
        state.lang = response;
        state.step = 'waiting_oneshots';
        sendTelegramReply(chatId, `✅ Idioma: ${state.lang}\n\n`
          + `*Paso 5/5*\n`
          + `¿Omitir capítulos oneshot?\n\n`
          + `  (s)í - Omitir capítulos promocionales/sin volumen\n`
          + `  (n)o - Incluir todos los capítulos\n\n`
          + `Predeterminado: s (sí)`);
      } else {
        sendTelegramReply(chatId, '❌ Idioma no válido.\n'
          + 'Opciones: es-la (español latino), en (inglés), es (español)\n\n'
          + 'Predeterminado: es-la');
      }
      break;

    case 'waiting_oneshots':
      if (response === 's' || response === 'si' || response === 'y' || response === '') {
        state.skipOneshots = true;
      } else if (response === 'n' || response === 'no') {
        state.skipOneshots = false;
      } else {
        sendTelegramReply(chatId, '❌ Respuesta no válida. Responde: s (sí) o n (no)');
        return;
      }
      state.step = 'ready';
      break;

    default:
      sendTelegramReply(chatId, '🔄 Sesión en estado desconocido. Usa /descargar <url> para reiniciar.');
      delete conversationStates[chatId];
      return;
  }

  // Si llegamos a 'ready', ejecutar
  if (state.step === 'ready') {
    executeDownload(chatId, state);
  }
}

function askLanguage(chatId, state) {
  const modeStr = state.mode === 'v' ? 'volumen' : 'capítulo';
  sendTelegramReply(chatId, `✅ ${modeStr.charAt(0).toUpperCase() + modeStr.slice(1)} final: ${state.end}\n\n`
    + `*Paso 4/5*\n`
    + `¿Idioma de traducción?\n\n`
    + `  es-la - Español (Latinoamérica)\n`
    + `  en - English\n`
    + `  es - Español (España)\n\n`
    + `Predeterminado: es-la`);
}

function executeDownload(chatId, state) {
  const mangaTitle = state.mangaUuid;

  // Disparar workflow
  const success = triggerGitHubWorkflow({
    url: state.url,
    mode: state.mode,
    start: state.start,
    end: state.end,
    lang: state.lang,
    skipOneshots: state.skipOneshots
  });

  if (success) {
    const modeStr = state.mode === 'v' ? 'Vol' : 'Cap';
    const skipStr = state.skipOneshots ? ' (omitiendo oneshots)' : '';
    sendTelegramReply(chatId,
      `✅ *Descarga iniciada*\n\n`
      + `📖 Manga: ${mangaTitle}\n`
      + `📦 ${modeStr} ${state.start}-${state.end}\n`
      + `🌐 Idioma: ${state.lang}${skipStr}\n\n`
      + `⏳ El archivo te llegará a Telegram cuando termine la conversión.\n`
      + `⏱️ Tiempo estimado: 5-15 minutos dependiendo del tamaño.`);
  } else {
    sendTelegramReply(chatId, `❌ Error al iniciar la descarga.\n\n`
      + `Verificá:\n`
      + `- Token de GitHub válido\n`
      + `- Workflow existe y está habilitado\n\n`
      + `Podés intentar de nuevo con /descargar ${state.url}`);
  }

  // Guardar en historial
  saveToHistory({
    title: mangaTitle,
    url: state.url,
    mode: state.mode,
    start: state.start,
    end: state.end,
    lang: state.lang,
    date: new Date().toISOString()
  });

  // Limpiar estado
  delete conversationStates[chatId];
}

// ---- HISTORIAL ----

function getHistory() {
  const props = PropertiesService.getScriptProperties();
  const historyJson = props.getProperty('DOWNLOAD_HISTORY');
  return historyJson ? JSON.parse(historyJson) : [];
}

function saveToHistory(item) {
  const props = PropertiesService.getScriptProperties();
  let history = getHistory();
  history.push(item);
  // Mantener solo los últimos 50
  if (history.length > 50) {
    history = history.slice(-50);
  }
  props.setProperty('DOWNLOAD_HISTORY', JSON.stringify(history));
}

// ---- PROCESAMIENTO PRINCIPAL ----

function processUpdates(data) {
  if (!data.ok || !data.result) return;

  for (const update of data.result) {
    lastUpdateId = Math.max(lastUpdateId, update.update_id);

    if (!update.message) continue;

    const chatId = update.message.chat.id.toString();
    const text = update.message.text || '';
    const props = getScriptProperties();

    // Validar que el mensaje viene del chat autorizado
    if (chatId !== props.TELEGRAM_CHAT_ID) continue;

    // Determinar si es un comando o respuesta interactiva
    if (text.startsWith('/')) {
      // Es un comando
      if (text.startsWith('/descargar')) {
        const urlMatch = text.match(/\/descargar\s+(.+)/i);
        handleDownload(chatId, urlMatch ? urlMatch[1].trim() : null);
      } else if (text === '/help' || text === '/start') {
        handleStart(chatId);
      } else if (text === '/status') {
        handleStatus(chatId);
      } else if (text === '/list') {
        handleList(chatId);
      } else if (text.startsWith('/cancel')) {
        const cancelMatch = text.match(/\/cancel\s*(.*)/i);
        handleCancel(chatId, cancelMatch ? cancelMatch[1] : '');
      } else {
        sendTelegramReply(chatId, '❌ Comando desconocido.\nUsa /help para ver los comandos disponibles.');
      }
    } else {
      // Es respuesta interactiva
      handleInteractiveResponse(chatId, text);
    }
  }
}

// ---- PUNTO DE ENTRADA (trigger cada 30 seg) ----

function main() {
  const data = getTelegramUpdates();
  if (data) {
    processUpdates(data);
  }
}

// Función de test (para probar manualmente)
function testBot() {
  const testMessage = {
    message: {
      chat: { id: PropertiesService.getScriptProperties().getProperty('TELEGRAM_CHAT_ID') },
      text: '/help'
    },
    update_id: 999999
  };

  console.log('Test: sending test message');
  sendTelegramMessage('🧪 *Test ejecutándose*\n\n'
    + 'Si ves este mensaje, el bot está funcionando correctamente.');
}