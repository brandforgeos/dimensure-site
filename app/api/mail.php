<?php
/*
 * Dimensure Portal — outgoing mail relay.
 * Called only by the portal's server functions (shared key). Sends branded emails as
 * surveys@dimensure.co.uk through the hosting account's own mail system.
 * Attachments are fetched from short-lived signed URLs, so large PDFs never pass through the request body.
 */
declare(strict_types=1);
header('Content-Type: application/json');
header('Cache-Control: no-store');
header('X-Robots-Tag: noindex');

$cfg = require dirname(__DIR__, 3) . '/dimensure-portal/config.php';

function out(int $code, array $body): void { http_response_code($code); echo json_encode($body); exit; }

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') out(405, ['ok' => false]);
$key = $_SERVER['HTTP_X_RELAY_KEY'] ?? '';
if (!hash_equals($cfg['relay_key'], $key)) out(401, ['ok' => false]);

$in = json_decode(file_get_contents('php://input') ?: '', true);
if (!is_array($in)) out(400, ['ok' => false, 'error' => 'bad json']);

$clean = static fn($v): string => trim(str_replace(["\r", "\n"], ' ', (string)$v));
$isEmail = static fn(string $e): bool => (bool)filter_var($e, FILTER_VALIDATE_EMAIL);

$to = array_values(array_filter(array_map($clean, (array)($in['to'] ?? [])), $isEmail));
$cc = array_values(array_filter(array_map($clean, (array)($in['cc'] ?? [])), $isEmail));
$bcc = array_values(array_filter(array_map($clean, (array)($in['bcc'] ?? [])), $isEmail));
if (!$to) out(422, ['ok' => false, 'error' => 'no recipients']);
$subject = $clean($in['subject'] ?? '');
if ($subject === '') out(422, ['ok' => false, 'error' => 'no subject']);

$fromAddr = $cfg['from_address'];
$fromName = $clean($in['from_name'] ?? 'Dimensure');
$replyTo = $clean($in['reply_to'] ?? $fromAddr);
if (!$isEmail($replyTo)) $replyTo = $fromAddr;
$html = (string)($in['html'] ?? '');
$text = (string)($in['text'] ?? strip_tags($html));
$messageId = '<' . bin2hex(random_bytes(12)) . '@dimensure.co.uk>';

$enc = static fn(string $s): string => preg_match('/^[\x20-\x7e]*$/', $s) ? $s : '=?UTF-8?B?' . base64_encode($s) . '?=';

// fetch attachments
$atts = [];
foreach ((array)($in['attachments'] ?? []) as $a) {
    $url = (string)($a['url'] ?? '');
    $name = preg_replace('/[^\w .,()\-]+/', '', (string)($a['name'] ?? 'attachment.pdf')) ?: 'attachment.pdf';
    if (!preg_match('#^https://' . preg_quote($cfg['supabase_host'], '#') . '/#', $url)) out(422, ['ok' => false, 'error' => 'attachment host']);
    $ch = curl_init($url);
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 60, CURLOPT_FOLLOWLOCATION => false]);
    $data = curl_exec($ch);
    $status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    curl_close($ch);
    if ($data === false || $status !== 200) out(502, ['ok' => false, 'error' => "attachment fetch $status"]);
    $atts[] = ['name' => $name, 'type' => (string)($a['type'] ?? 'application/pdf'), 'data' => $data];
}

$alt = 'alt_' . bin2hex(random_bytes(8));
$mix = 'mix_' . bin2hex(random_bytes(8));
$altPart = "Content-Type: multipart/alternative; boundary=\"$alt\"\r\n\r\n"
    . "--$alt\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($text)) . "\r\n"
    . "--$alt\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($html)) . "\r\n"
    . "--$alt--";

$headers = [
    'From: ' . $enc($fromName) . " <$fromAddr>",
    "Reply-To: $replyTo",
    "Message-ID: $messageId",
    'MIME-Version: 1.0',
];
if ($cc) $headers[] = 'Cc: ' . implode(', ', $cc);
if ($bcc) $headers[] = 'Bcc: ' . implode(', ', $bcc);
if (!empty($in['thread_key'])) $headers[] = 'X-Dimensure-Ref: ' . $clean($in['thread_key']);

if ($atts) {
    $headers[] = "Content-Type: multipart/mixed; boundary=\"$mix\"";
    $body = "--$mix\r\n$altPart\r\n";
    foreach ($atts as $a) {
        $body .= "--$mix\r\nContent-Type: {$a['type']}; name=\"{$a['name']}\"\r\nContent-Transfer-Encoding: base64\r\n"
            . "Content-Disposition: attachment; filename=\"{$a['name']}\"\r\n\r\n" . chunk_split(base64_encode($a['data'])) . "\r\n";
    }
    $body .= "--$mix--";
} else {
    [$ctLine, $rest] = explode("\r\n\r\n", $altPart, 2);
    $headers[] = $ctLine;
    $body = $rest;
}

$sent = mail(implode(', ', $to), $enc($subject), $body, implode("\r\n", $headers), '-f' . $fromAddr);
out($sent ? 200 : 500, ['ok' => $sent, 'message_id' => $messageId]);
