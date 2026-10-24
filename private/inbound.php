#!/usr/bin/php -q
<?php
/*
 * Dimensure Portal — incoming mail pipe.
 * The dimensure.co.uk catch-all pipes mail here. Only project addresses (dim-1234@dimensure.co.uk)
 * are passed to the portal; everything else is dropped quietly. A copy of every accepted email is
 * forwarded to surveys@ so it is also in the normal inbox.
 * Must print nothing: any output becomes a bounce.
 */
declare(strict_types=1);
error_reporting(0);
$cfg = require __DIR__ . '/config.php';

$raw = stream_get_contents(STDIN);
if ($raw === false || $raw === '' || strlen($raw) > 40 * 1024 * 1024) exit(0);

// Which addresses was it sent to? (envelope recipient is not available, so read the headers)
[$head] = explode("\r\n\r\n", str_replace("\n", "\r\n", str_replace("\r\n", "\n", $raw)), 2) + [''];
$head = preg_replace("/\r\n[ \t]+/", ' ', $head);
$targets = [];
foreach (explode("\r\n", $head) as $line) {
    if (preg_match('/^(to|cc|delivered-to|x-original-to|envelope-to):(.*)$/i', $line, $m)) {
        if (preg_match_all('/dim-(\d{3,6})@dimensure\.co\.uk/i', $m[2], $mm)) {
            foreach ($mm[1] as $n) $targets['DIM-' . $n] = true;
        }
    }
}
if (!$targets) exit(0);   // not a project address — drop

$ch = curl_init($cfg['inbound_url']);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_TIMEOUT => 120,
    CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'x-inbound-key: ' . $cfg['inbound_key']],
    CURLOPT_POSTFIELDS => json_encode(['projects' => array_keys($targets), 'raw_b64' => base64_encode($raw)]),
]);
curl_exec($ch);
curl_close($ch);

// copy to the shared inbox
if (!empty($cfg['copy_to'])) {
    $fwdHeaders = "From: Dimensure Portal <{$cfg['from_address']}>\r\nMIME-Version: 1.0\r\nContent-Type: message/rfc822";
    @mail($cfg['copy_to'], 'Portal mail received: ' . implode(', ', array_keys($targets)), $raw, $fwdHeaders, '-f' . $cfg['from_address']);
}
exit(0);
