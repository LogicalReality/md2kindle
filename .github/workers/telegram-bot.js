/**
 * md2kindle Telegram Bot — Cloudflare Worker
 *
 * Recibe comandos de Telegram y dispara el workflow de GitHub Actions.
 *
 * Variables de entorno requeridas (Cloudflare Secrets):
 *   TELEGRAM_TOKEN   — Token del bot (BotFather)
 *   TELEGRAM_CHAT_ID — Tu chat ID personal (seguridad)
 *   GITHUB_PAT       — GitHub Personal Access Token (scope: workflow)
 *
 * Comando disponible:
 *   /manga <url> <modo> <inicio> [fin] [idioma]
 *
 * Ejemplos:
 *   /manga https://mangadex.org/title/xxx v 1
 *   /manga https://mangadex.org/title/xxx v 1 5
 *   /manga https://mangadex.org/title/xxx v 1 5 en
 *   /manga https://mangadex.org/title/xxx c 10 20 es-la
 */

const GITHUB_OWNER = "LogicalReality";
const GITHUB_REPO  = "md2kindle";
const GITHUB_WORKFLOW = "kindle-delivery.yml";
const GITHUB_REF  = "main";

export default {
  async fetch(request, env) {
    // Solo aceptamos POST (webhooks de Telegram)
    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return new Response("Bad Request", { status: 400 });
    }

    const message = body?.message;
    const chatId  = String(message?.chat?.id ?? "");
    const text    = message?.text?.trim() ?? "";

    // Ignorar silenciosamente mensajes de otros chats
    if (chatId !== env.TELEGRAM_CHAT_ID) {
      return new Response("ok");
    }

    // Solo procesamos el comando /manga
    if (!text.startsWith("/manga")) {
      await sendMessage(env, chatId, helpText());
      return new Response("ok");
    }

    // Parsear argumentos: /manga <url> <modo> <inicio> [fin] [idioma]
    const parts = text.split(/\s+/);
    const url   = parts[1];
    const mode  = parts[2] ?? "v";
    const start = parts[3] ?? "1";
    const end   = parts[4] ?? "";
    const lang  = parts[5] ?? "es-la";

    if (!url) {
      await sendMessage(env, chatId, "❌ Falta la URL.\n\nUso: `/manga <url> <modo> <inicio> [fin] [idioma]`");
      return new Response("ok");
    }

    // Construir inputs del workflow
    const inputs = {
      url,
      mode,
      start,
      lang,
      skip_oneshots: "true",
    };
    if (end) inputs.end = end;

    // Disparar el workflow en GitHub
    const ghRes = await fetch(
      `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/${GITHUB_WORKFLOW}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GITHUB_PAT}`,
          Accept: "application/vnd.github+json",
          "Content-Type": "application/json",
          "User-Agent": "md2kindle-telegram-bot",
        },
        body: JSON.stringify({ ref: GITHUB_REF, inputs }),
      }
    );

    if (ghRes.status === 204) {
      const rangeText = end ? ` al ${end}` : "";
      const reply = [
        `⚙️ *Workflow iniciado*`,
        ``,
        `📖 Modo: *${mode === "v" ? "Volumen" : "Capítulo"}* ${start}${rangeText}`,
        `🌐 Idioma: *${lang}*`,
        ``,
        `Te enviaré el .mobi cuando esté listo.`,
      ].join("\n");
      await sendMessage(env, chatId, reply);
    } else {
      const errBody = await ghRes.text();
      await sendMessage(
        env,
        chatId,
        `❌ Error al contactar GitHub (${ghRes.status}):\n\`${errBody}\``
      );
    }

    return new Response("ok");
  },
};

// ─── Helpers ────────────────────────────────────────────────────────────────

async function sendMessage(env, chatId, text) {
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: "Markdown",
    }),
  });
}

function helpText() {
  return [
    "🤖 *md2kindle Bot*",
    "",
    "Uso: `/manga <url> <modo> <inicio> [fin] [idioma]`",
    "",
    "*Modos:*",
    "  `v` — Volumen (default)",
    "  `c` — Capítulo",
    "",
    "*Idiomas:* `es-la` (default) · `en` · `es`",
    "",
    "*Ejemplos:*",
    "`/manga https://mangadex.org/title/xxx v 1`",
    "`/manga https://mangadex.org/title/xxx v 1 5`",
    "`/manga https://mangadex.org/title/xxx c 10 20 en`",
  ].join("\n");
}
