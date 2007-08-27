<?php
// Send a mail as UTF-8.
function sendMail($toName, $toEmail, $body) {
	$to       = "=?UTF-8?B?" . base64_encode($toName) . "?= <$toEmail>";
	$subject  = "=?UTF-8?B?" . base64_encode("HTML5 Status Update") . "?=";
	$sig      = "HTML5 Status Updates\r\nhttp://www.w3.org/html/\r\nhttp://www.whatwg.org/";
	$message  = "$body\r\n-- \r\n$sig";
	$headers  = "MIME-Version: 1.0\r\n";
	$headers .= "Content-Type: text/plain; charset=utf-8; format=flowed\r\n";
	$headers .= "From: =?UTF-8?B?" . base64_encode("HTML5 Status") . "?= <whatwg@whatwg.org>";
	
	mail($to, $subject, $message, $headers);
}
?>