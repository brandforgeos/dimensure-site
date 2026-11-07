<?php
/*
 * Dimensure Portal — file relay.
 * Every file the portal opens (drawings, drafts, issued reports, flow models) is shown from app.dimensure.co.uk,
 * never from the storage address. The portal (or a server function) makes a short-lived signed storage link as
 * before and passes it here; this script checks it is a signed link for the Dimensure storage project only,
 * fetches it and streams it back with its proper file name.
 *
 *   /api/file.php/<file name>?u=<signed storage URL>[&d=1]
 *     <file name>  shown/saved name (path form, so every browser and iPhone keeps it); ?n= also accepted
 *     d=1          save the file (attachment) instead of opening it
 *
 * Access control is the signed link itself: it is only issued to someone allowed to see the file and expires
 * within minutes. This script holds no keys and can reach nothing but signed objects in the one project.
 */
declare(strict_types=1);

const PROJECT_HOST = 'ivmdqsxnnstvxcspdmov.supabase.co';
const SIGN_PREFIX = '/storage/v1/object/sign/';

header('X-Robots-Tag: noindex, nofollow');
header('Referrer-Policy: no-referrer');
header('X-Content-Type-Options: nosniff');

function stop(int $code, string $msg): void {
    http_response_code($code);
    header('Content-Type: text/html; charset=utf-8');
    header('Cache-Control: no-store');
    $m = htmlspecialchars($msg, ENT_QUOTES);
    echo "<!doctype html><meta charset=utf-8><meta name=viewport content=\"width=device-width,initial-scale=1\"><title>Dimensure</title>"
       . "<body style=\"font:16px/1.5 system-ui,-apple-system,sans-serif;color:#0d1b2a;max-width:32rem;margin:15vh auto;padding:0 16px\">"
       . "<h1 style=\"font-size:20px\">File not available</h1><p>$m</p><p><a href=\"/\">Back to the portal</a></p>";
    exit;
}

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if ($method !== 'GET' && $method !== 'HEAD') { header('Allow: GET, HEAD'); stop(405, 'This address only opens files.'); }

// ── 1. the signed link: only https://<project>/storage/v1/object/sign/<bucket>/<path>?token=…[&download=…]
$u = (string)($_GET['u'] ?? '');
if ($u === '' || strlen($u) > 4096) stop(400, 'This link is not complete. Please open the file again from the portal.');
$p = parse_url($u);
if (!is_array($p)
    || ($p['scheme'] ?? '') !== 'https'
    || strtolower($p['host'] ?? '') !== PROJECT_HOST
    || isset($p['port']) || isset($p['user']) || isset($p['pass']) || isset($p['fragment'])) {
    stop(403, 'This link is not a Dimensure file link.');
}
$path = (string)($p['path'] ?? '');
if (strncmp($path, SIGN_PREFIX, strlen(SIGN_PREFIX)) !== 0) stop(403, 'This link is not a Dimensure file link.');
$object = substr($path, strlen(SIGN_PREFIX));                       // <bucket>/<path, url-encoded>
$decoded = rawurldecode($object);
if (!preg_match('#^[a-z0-9][a-z0-9_-]{1,62}/[^\x00-\x1f\\\\]+$#', $decoded)
    || preg_match('#(^|/)\.\.?(/|$)#', $decoded) || strpos($decoded, '//') !== false) {
    stop(403, 'This link is not a Dimensure file link.');
}
parse_str((string)($p['query'] ?? ''), $q);
foreach (array_keys($q) as $k) if ($k !== 'token' && $k !== 'download') stop(403, 'This link is not a Dimensure file link.');
$token = (string)($q['token'] ?? '');
if (!preg_match('/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/', $token)) stop(403, 'This link is not a Dimensure file link.');
// rebuild the upstream address from checked parts only (download= is dropped: this script sets the disposition)
$upstream = 'https://' . PROJECT_HOST . SIGN_PREFIX . $object . '?token=' . rawurlencode($token);

// ── 2. the file name: path form first, then ?n=, then the link's own download name, then the stored name
$name = '';
if (!empty($_SERVER['PATH_INFO'])) $name = ltrim((string)$_SERVER['PATH_INFO'], '/');
if ($name === '' && isset($_GET['n'])) $name = (string)$_GET['n'];
if ($name === '' && isset($q['download']) && $q['download'] !== '') $name = (string)$q['download'];
if ($name === '') $name = basename($decoded);
$name = trim(preg_replace('/[\x00-\x1f\x7f\/\\\\"]+/u', ' ', $name) ?? '', " .\t");
if ($name === '' || !preg_match('//u', $name)) $name = 'file';
$name = preg_replace('/^(.{0,180}).*$/us', '$1', $name);
$ext = strtolower(pathinfo($name, PATHINFO_EXTENSION));
if ($ext === '') {                                                   // keep the stored file's extension
    $ext = strtolower(pathinfo($decoded, PATHINFO_EXTENSION));
    if ($ext !== '') $name .= '.' . $ext;
}
$download = ($_GET['d'] ?? '') === '1';

$TYPES = [
    'pdf' => 'application/pdf', 'png' => 'image/png', 'jpg' => 'image/jpeg', 'jpeg' => 'image/jpeg', 'gif' => 'image/gif',
    'webp' => 'image/webp', 'heic' => 'image/heic', 'svg' => 'image/svg+xml', 'tif' => 'image/tiff', 'tiff' => 'image/tiff',
    'html' => 'text/html; charset=utf-8', 'htm' => 'text/html; charset=utf-8', 'txt' => 'text/plain; charset=utf-8',
    'csv' => 'text/csv; charset=utf-8', 'json' => 'application/json', 'xml' => 'application/xml',
    'dwg' => 'application/acad', 'dxf' => 'image/vnd.dxf', 'zip' => 'application/zip',
    'xlsx' => 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xls' => 'application/vnd.ms-excel',
    'docx' => 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'doc' => 'application/msword',
    'mp4' => 'video/mp4', 'mov' => 'video/quicktime',
];

// ── 3. fetch and stream. Headers are sent once the storage reply's headers are in; the body is passed straight through.
@set_time_limit(0);
while (ob_get_level() > 0) ob_end_clean();
$range = $_SERVER['HTTP_RANGE'] ?? '';
$st = ['code' => 0, 'type' => '', 'len' => '', 'crange' => '', 'sent' => false, 'err' => ''];

$ch = curl_init($upstream);
curl_setopt_array($ch, [
    CURLOPT_FOLLOWLOCATION => false,
    CURLOPT_CONNECTTIMEOUT => 15,
    CURLOPT_TIMEOUT => 0,
    CURLOPT_LOW_SPEED_LIMIT => 1, CURLOPT_LOW_SPEED_TIME => 60,
    CURLOPT_NOBODY => $method === 'HEAD',
    CURLOPT_PROTOCOLS => CURLPROTO_HTTPS,
    CURLOPT_HTTPHEADER => array_values(array_filter([
        'Accept: */*',
        preg_match('/^bytes=\d*-\d*(,\s*\d*-\d*)*$/', $range) ? "Range: $range" : null,
    ])),
    CURLOPT_HEADERFUNCTION => static function ($c, string $line) use (&$st): int {
        $len = strlen($line);
        if (preg_match('#^HTTP/\S+\s+(\d{3})#', $line, $m)) { $st['code'] = (int)$m[1]; return $len; }
        $h = explode(':', $line, 2);
        if (count($h) === 2) {
            $k = strtolower(trim($h[0])); $v = trim($h[1]);
            if ($k === 'content-type') $st['type'] = $v;
            elseif ($k === 'content-length') $st['len'] = $v;
            elseif ($k === 'content-range') $st['crange'] = $v;
        }
        return $len;
    },
    CURLOPT_WRITEFUNCTION => static function ($c, string $chunk) use (&$st, $name, $ext, $download, $TYPES): int {
        if (!$st['sent']) {
            if ($st['code'] !== 200 && $st['code'] !== 206) { $st['err'] .= substr($chunk, 0, 2000); return strlen($chunk); }
            send_headers($st, $name, $ext, $download, $TYPES);
        }
        echo $chunk;
        flush();
        return connection_aborted() ? 0 : strlen($chunk);
    },
]);
$ok = curl_exec($ch);
$cerr = curl_errno($ch);
curl_close($ch);

if (!$st['sent']) {
    if ($st['code'] === 200 || $st['code'] === 206) { send_headers($st, $name, $ext, $download, $TYPES); exit; } // empty file / HEAD
    if ($st['code'] === 416) { http_response_code(416); header('Content-Range: ' . ($st['crange'] ?: 'bytes */*')); exit; }
    if ($ok === false && $cerr) stop(502, 'The file could not be reached just now. Please try again in a moment.');
    if ($st['code'] === 400 || $st['code'] === 401 || $st['code'] === 403) {
        stop(410, 'This file link has expired. Please go back to the portal and open the file again.');
    }
    if ($st['code'] === 404) stop(404, 'This file could not be found. Please go back to the portal and open it again.');
    stop(502, 'The file could not be opened just now. Please try again in a moment.');
}
exit;

function send_headers(array &$st, string $name, string $ext, bool $download, array $TYPES): void {
    $st['sent'] = true;
    http_response_code($st['code']);
    $type = strtolower($st['type']);
    if ($type === '' || strncmp($type, 'application/octet-stream', 24) === 0 || strncmp($type, 'binary/', 7) === 0 || strncmp($type, 'text/plain', 10) === 0) {
        $type = $TYPES[$ext] ?? ($type ?: 'application/octet-stream');
    }
    header('Content-Type: ' . $type);
    if ($st['len'] !== '' && ctype_digit($st['len'])) header('Content-Length: ' . $st['len']);
    if ($st['crange'] !== '') header('Content-Range: ' . $st['crange']);
    header('Accept-Ranges: bytes');
    $ascii = preg_replace('/[^\x20-\x7e]/', '_', $name) ?: 'file';
    header(sprintf('Content-Disposition: %s; filename="%s"; filename*=UTF-8\'\'%s', $download ? 'attachment' : 'inline', $ascii, rawurlencode($name)));
    header('Cache-Control: private, no-store, max-age=0');
    // HTML/SVG/XML (flow models, uploads) open in a sandbox with their own origin, so a file can never act as the portal
    if (preg_match('#^(text/html|image/svg\+xml|application/xml|text/xml|application/xhtml)#', $type)) {
        header("Content-Security-Policy: sandbox allow-scripts allow-popups allow-popups-to-escape-sandbox allow-downloads allow-modals allow-forms; frame-ancestors 'self'");
    }
}
