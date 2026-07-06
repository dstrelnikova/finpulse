export async function openExternalUrl(url: string) {
  if (!url) return;

  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return;
  }

  if (!["http:", "https:"].includes(parsed.protocol)) {
    return;
  }

  try {
    const { openUrl } = await import("@tauri-apps/plugin-opener");
    await openUrl(parsed.toString());
    return;
  } catch {
    window.open(parsed.toString(), "_blank", "noopener,noreferrer");
  }
}
