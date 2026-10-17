<?php
// Submits every URL in sitemap.xml to IndexNow (Bing, Yandex, Seznam, Naver).
// Run by visiting /indexnow.php?run=4a6eb4b185101a3a90873219 after a deploy.
header('Content-Type: text/plain'); header('X-Robots-Tag: noindex');
if (($_GET['run'] ?? '') !== '4a6eb4b185101a3a90873219') { http_response_code(404); exit; }
$key = '8a856c348619c93de03dacd65114e28a';
preg_match_all('#<loc>([^<]+)</loc>#', (string)file_get_contents(__DIR__ . '/sitemap.xml'), $m);
$body = json_encode(['host' => 'dimensure.co.uk', 'key' => $key,
  'keyLocation' => "https://dimensure.co.uk/$key.txt", 'urlList' => $m[1]]);
$ch = curl_init('https://api.indexnow.org/indexnow');
curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_POSTFIELDS => $body, CURLOPT_RETURNTRANSFER => true,
  CURLOPT_HTTPHEADER => ['Content-Type: application/json; charset=utf-8'], CURLOPT_TIMEOUT => 20]);
$out = curl_exec($ch);
echo 'IndexNow HTTP ' . curl_getinfo($ch, CURLINFO_HTTP_CODE) . ' for ' . count($m[1]) . " URLs\n" . $out;
