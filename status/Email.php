<?php
require_once "encoding-functions.php";

class Email {
	var $headers = array();
	var $to = array();
	var $cc = array();
	var $bcc = array();
	var $from = '';

	var $subject = '';
	var $body = '';
	var $sig = '';

	function Email() {
		$this->headers['MIME-Version'] = 'MIME-Version: 1.0';
		$this->headers['Content-Type'] = 'Content-Type: text/plain; charset=UTF-8; format=flowed';
	}

	// Private Functions
	function address($name, $address) {
		$fieldValue = '';
		if (isValidEmail($address)) {
			if ($name != '') {
				$fieldValue  = isASCII($name) ? '"'.addcslashes($name, '"\\').'"' : '=?UTF-8?B?' . base64_encode($name) . '?=';
				$fieldValue .= " <$address>";
			} else {
				$fieldValue = $address;
			}
		}
		return $fieldValue;
	}

	function preserve_wordwrap($str, $width = 72, $break = "\n", $cut = false) {
		// Note: this does not correctly deal with wrapping quoted lines beginning with: >
		$linewrap = create_function('$l', 'return wordwrap($l, ' . $width . ', ' . var_export($break, true) . ', ' . var_export($cut, true) . ');');

		$lines = explode("\n", $str);
		$lines = array_map($linewrap, $lines);
		return implode("\n", $lines);
	}


	// Public Functions
	function addRecipient($type, $name, $email) {
		$fieldValue = $this->address($name, $email);

		if ($fieldValue != '') {
			switch (strtolower($type)) {
			case 'to':
				array_push($this->to, $fieldValue);
				break;
			case 'cc':
				array_push($this->cc, $fieldValue);
				break;
			case 'bcc':
				array_push($this->bcc, $fieldValue);
				break;
			}
		}
	}

	function setFrom($name, $address) {
		$this->from = $this->address($name, $address);
	}

	function setSubject($text) {
		$this->subject = preg_replace("/(\r\n|\r|\n)/", " ", $text); // Strip line breaks
		$this->subject = isASCII($this->subject) ? $text : '=?UTF-8?B?' . base64_encode($this->subject) . '?=';
	}

	function setSignature($text) {
		// strip trailing spaces and normalize linebreaks
		$this->sig = preg_replace("/ *(\r\n|\r|\n)/", "\n", $text);
	}

	function setText($text) {
		// strip trailing spaces and normalize linebreaks
		$this->body = preg_replace("/ *(\r\n|\r|\n)/", "\n", $text);
	}

	function send() {
		$headerFields = implode("\r\n", $this->headers);

		if (count($this->to) > 0) {
			$toField = implode(", \r\n\t", $this->to);
		}

		if (count($this->cc) > 0) {
			$headerFields .= "\r\nCc: " . implode(", \r\n\t", $this->cc);
		}

		if (count($this->bcc) > 0) {
			$headerFields .= "\r\nBcc: " . implode(", \r\n\t", $this->bcc);
		}

		if ($this->from != '') {
			$headerFields .= "\r\nFrom: $this->from";
		}

		$message = $this->preserve_wordwrap("$this->body\n-- \n$this->sig", 72, " \n", false);
		$message = $this->preserve_wordwrap($message, 990, "\n", true);
		$message = preg_replace("/(^|\r\n|\n)(>| |From )/", "$1 $2", $message); // space-stuffing

		// Use this for debugging
		// echo "To: $toField\nSubject: $this->subject\n$headerFields\n\n$message";

		mail($toField, $this->subject, $message, $headerFields);
	}
}

function isValidEmail($email) {
	$pattern = "/^[a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i";
	return preg_match($pattern, $email);
}

// Old function, to be removed later
// Send a mail as UTF-8.
/*
function sendMail($toName, $toEmail, $body) {
	if (isValidEmail($toEmail)) {
		$to       = "=?UTF-8?B?" . base64_encode($toName) . "?= <$toEmail>";
		$subject  = "=?UTF-8?B?" . base64_encode("HTML5 Status Update") . "?=";
		$sig      = "HTML5 Status Updates\r\nhttp://www.w3.org/html/\r\nhttp://www.whatwg.org/";
		$body     = preg_replace("/ *(\r\n|\r|\n)/", "\r\n", $body); // strip trailing spaces and normalize linebreaks
		// XXX change wordwrap to utf8_wordwrap on the next 2 lines
		$body     = wordwrap($body, 72, ' \r\n', false); // soft linebreaks, but preserve words longer than 72 characters
		$body     = wordwrap($body, 990, '\r\n', true);
		$body     = preg_replace("/(^|\r\n)(>| |From )/", "$1 $2", $body); // space-stuffing
		$message  = "$body\r\n-- \r\n$sig";
		$headers  = "MIME-Version: 1.0\r\n";
		$headers .= "Content-Type: text/plain; charset=utf-8; format=flowed\r\n";
		$headers .= "From: =?UTF-8?B?" . base64_encode("HTML5 Status") . "?= <whatwg@whatwg.org>";

		mail($to, $subject, $message, $headers);
	}
}
*/
?>