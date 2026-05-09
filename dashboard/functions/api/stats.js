export async function onRequest(context) {
  const db = context.env.DB;

  if (!db) {
    return new Response(JSON.stringify({ error: "D1 Database binding 'DB' not found" }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }

  try {
    // 1. Total Downloads & Total Size
    const summaryStmt = await db.prepare(
      "SELECT COUNT(*) as total_downloads, SUM(size_mb) as total_size_mb FROM downloads"
    ).first();

    const totalDownloads = summaryStmt?.total_downloads || 0;
    const totalSizeGB = summaryStmt?.total_size_mb ? (summaryStmt.total_size_mb / 1024).toFixed(2) : 0;

    // 2. Method Distribution
    const methodsStmt = await db.prepare(
      "SELECT method, COUNT(*) as count FROM downloads GROUP BY method"
    ).all();
    const methodDistribution = methodsStmt.results || [];

    // 3. Recent Activity (last 10)
    const recentStmt = await db.prepare(
      "SELECT manga, volume, lang, size_mb, method, delivered_at FROM downloads ORDER BY delivered_at DESC LIMIT 10"
    ).all();
    const recentActivity = recentStmt.results || [];

    // 4. Daily Stats (last 30 days)
    const dailyStmt = await db.prepare(`
      SELECT date(delivered_at) as day, COUNT(*) as count 
      FROM downloads 
      WHERE date(delivered_at) >= date('now', '-30 days')
      GROUP BY day 
      ORDER BY day ASC
    `).all();
    const dailyStats = dailyStmt.results || [];

    const stats = {
      total_downloads: totalDownloads,
      total_size_gb: totalSizeGB,
      method_distribution: methodDistribution,
      recent_activity: recentActivity,
      daily_stats: dailyStats
    };

    return new Response(JSON.stringify(stats), {
      status: 200,
      headers: { 
        "Content-Type": "application/json",
        // Simple CORS if needed
        "Access-Control-Allow-Origin": "*"
      }
    });

  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
}
