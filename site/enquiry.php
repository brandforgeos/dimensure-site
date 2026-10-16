<?php
/*
 * Dimensure website enquiry handler.
 * Receives the contact form, keeps a copy of every enquiry outside the web root,
 * and emails it to info@dimensure.co.uk from website@dimensure.co.uk.
 */
declare(strict_types=1);

const TO_EMAIL   = 'info@dimensure.co.uk';
const FROM_EMAIL = 'website@dimensure.co.uk';
const FROM_NAME  = 'Dimensure Website';
const MAX_PER_HOUR = 10;   // per sending IP address

header('Content-Type: application/json');
header('Cache-Control: no-store');
header('X-Robots-Tag: noindex');

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405);
    echo '{"ok":false}';
    exit;
}

// Leads are stored next to public_html, never inside it.
$home = getenv('HOME') ?: dirname(__DIR__, 2);
$leadsDir = rtrim($home, '/') . '/dimensure-leads';
if (!is_dir($leadsDir . '/rate')) {
    @mkdir($leadsDir . '/rate', 0700, true);
}

$f = static function (string $key, int $max = 500): string {
    $v = trim((string)($_POST[$key] ?? ''));
    return mb_substr($v, 0, $max);
};
$oneLine = static fn(string $v): string => str_replace(["\r", "\n"], ' ', $v);

// Honeypot: real people never fill the hidden "website" field.
if ($f('website') !== '') {
    echo '{"ok":true}';
    exit;
}

$lead = [
    'received' => gmdate('c'),
    'name'     => $f('name', 100),
    'company'  => $f('company', 120),
    'email'    => $f('email', 160),
    'phone'    => $f('phone', 40),
    'service'  => $f('service', 80),
    'location' => $f('location', 120),
    'message'  => $f('message', 4000),
    'page'     => $f('page', 200),
];

if ($lead['name'] === '' || $lead['message'] === '' || !filter_var($lead['email'], FILTER_VALIDATE_EMAIL)) {
    http_response_code(422);
    echo '{"ok":false,"error":"missing"}';
    exit;
}

// Simple rate limit.
$ip = preg_replace('/[^0-9a-f:.]/i', '', (string)($_SERVER['REMOTE_ADDR'] ?? 'x'));
$rateFile = $leadsDir . '/rate/' . md5($ip . '|' . gmdate('YmdH'));
$count = (int)@file_get_contents($rateFile) + 1;
@file_put_contents($rateFile, (string)$count);
if ($count > MAX_PER_HOUR) {
    http_response_code(429);
    echo '{"ok":false,"error":"rate"}';
    exit;
}

$saved = @file_put_contents(
    $leadsDir . '/' . gmdate('Ymd-His') . '-' . bin2hex(random_bytes(3)) . '.json',
    json_encode($lead, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
) !== false;

$labels = [
    'name' => 'Name', 'company' => 'Company', 'email' => 'Email', 'phone' => 'Phone',
    'service' => 'Service', 'location' => 'Site town or postcode', 'message' => 'Message',
    'page' => 'Sent from page', 'received' => 'Received (UTC)',
];
$body = "New enquiry from the Dimensure website.\n\nReply to this email to answer them directly.\n\n";
foreach ($labels as $k => $label) {
    if ($lead[$k] !== '') {
        $body .= $k === 'message' ? "\n$label:\n{$lead[$k]}\n\n" : "$label: {$lead[$k]}\n";
    }
}

$subject = 'Website enquiry: ' . $oneLine($lead['service'] ?: 'General') . ' - ' . $oneLine($lead['name']);
$headers = implode("\r\n", [
    'From: ' . FROM_NAME . ' <' . FROM_EMAIL . '>',
    'Reply-To: ' . $oneLine($lead['name']) . ' <' . $oneLine($lead['email']) . '>',
    'Content-Type: text/plain; charset=UTF-8',
    'X-Mailer: PHP',
]);
$sent = @mail(
    TO_EMAIL,
    '=?UTF-8?B?' . base64_encode($subject) . '?=',
    $body,
    $headers,
    '-f' . FROM_EMAIL
);

echo json_encode(['ok' => $saved || $sent]);
