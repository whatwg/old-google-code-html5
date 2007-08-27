<?php
function utf8_wordwrap($str,$len,$what){ // XXX need a forth argument, $cut = true, just like wordwrap()
	# usage: utf8_wordwrap("text",3,"<br>");
	# by tjomi4`, thanks to SiMM.
	# www.yeap.lv
	$from=0;
	$str_length = preg_match_all('/[\x00-\x7F\xC0-\xFD]/', $str, $var_empty);
	$while_what = $str_length / $len;
	while($i <= round($while_what)){
		$string = preg_replace('#^(?:[\x00-\x7F]|[\xC0-\xFF][\x80-\xBF]+){0,'.$from.'}'.
							   '((?:[\x00-\x7F]|[\xC0-\xFF][\x80-\xBF]+){0,'.$len.'}).*#s',
							   '$1',$str);
		$total .= $string.$what;
		$from = $from+$len;
		$i++;
	}
	return $total;
}


// Send a mail as UTF-8.
function sendMail($toName, $toEmail, $body) {
	$to       = "=?UTF-8?B?" . base64_encode($toName) . "?= <$toEmail>";
	$subject  = "=?UTF-8?B?" . base64_encode("HTML5 Status Update") . "?=";
	$sig      = "HTML5 Status Updates\r\nhttp://www.w3.org/html/\r\nhttp://www.whatwg.org/";
	$body     = preg_replace("/ *(\r\n|\r|\n)/", "\r\n", $body); // strip trailing spaces and normalize linebreaks
	// XXX change wordwrap to utf8_wordwrap on the next 2 lines
	$body     = wordwrap($body, 72, ' \r\n', false); // soft linebreaks, but preserve words longer than 72 characters
	$body     = wordwrap($body, 998, ' \r\n', true); // soft linebreak for words longer than 998 characters (XXX not clear from rfc2646 if this is correct)
	$body     = preg_replace("/(^|\r\n)(>| |From )/", "$1 $2", $body); // space-stuffing
	$message  = "$body\r\n-- \r\n$sig";
	$headers  = "MIME-Version: 1.0\r\n";
	$headers .= "Content-Type: text/plain; charset=utf-8; format=flowed\r\n";
	$headers .= "From: =?UTF-8?B?" . base64_encode("HTML5 Status") . "?= <whatwg@whatwg.org>";
	
	mail($to, $subject, $message, $headers);
}
?>