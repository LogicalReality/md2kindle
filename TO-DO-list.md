# TO-DO List

- [x] TO-DO: Verificar la estabilidad con mangas que tengan múltiples autores o ninguno tras los cambios en la API. (Completado: 2026-03-31)
- [x] TO-DO: Considerar la automatización de la selección de volumen si la URL apunta a un volumen específico en el futuro. (Completado: 2026-03-31)
- [x] TO-DO: Implementar entrega automática (Telegram/ffsend E2EE) y GitHub Actions. (Completado: 2026-03-31)

## Futuras Mejoras (Edge Cases)

- [x] TO-DO: Soporte para capítulos alfanuméricos (Ej: 10a, 20b). (Completado: 2026-03-31)
- [x] TO-DO: Evitar borrado de volúmenes con nombres especiales ("S", "Extra"). (Completado: 2026-03-31)
- [x] TO-DO: Auditoría de descarga (Avisar si faltan capítulos en el rango). (Completado: 2026-03-31)
- [x] TO-DO: Fallback de Título con UUID si el nombre sanitizado queda vacío. (Completado: 2026-03-31)
- [ ] TO-DO: Extraer main() en funciones testables (download_flow, convert_flow, telegram_flow)
- [x] TO-DO: Modificar mensaje del bot de Telegram para mostrar el nombre real del manga (actualmente solo dice "Manga") (Completado: 2026-04-22)
- [x] TO-DO: Mostrar el nombre del manga en los archivos .mobi generados (actualmente no incluye el título en los metadatos del archivo) (Completado: 2026-04-22)
