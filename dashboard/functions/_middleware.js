export async function onRequest(context) {
  // Pass-through for local development if DASHBOARD_PASSWORD is not set
  if (!context.env.DASHBOARD_PASSWORD) {
    return await context.next();
  }

  const authHeader = context.request.headers.get("Authorization");
  if (!authHeader) {
    return new Response("Unauthorized", {
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="md2kindle Dashboard", charset="UTF-8"',
      },
    });
  }

  // Basic auth is "Basic base64(user:password)"
  const [scheme, encoded] = authHeader.split(" ");
  if (scheme !== "Basic" || !encoded) {
    return new Response("Bad Request", { status: 400 });
  }

  const decoded = atob(encoded);
  const [username, password] = decoded.split(":");

  // We only check the password against the environment variable
  if (password !== context.env.DASHBOARD_PASSWORD) {
    return new Response("Unauthorized", {
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="md2kindle Dashboard", charset="UTF-8"',
      },
    });
  }

  return await context.next();
}
