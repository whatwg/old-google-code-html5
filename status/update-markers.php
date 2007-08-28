<?php
header("Content-Type: text/html; charset=UTF-8");
require_once "Email.php";
require_once "encoding-functions.php";

/*
 * IMPORTANT: when testing for yourself, change the email address to your own
 *            in the call to $mail->addRecipient(...)
 *
 * TODO:
 *
 * Twitter message: "Status Update: $rationale"
 * 
 * Finish writing the code to send appropriate emails
 * - Confirmation requests probably to Hixie
 * - Confirmed status updates to commit-watches
 * Write the confirmation system to check in updates to the DB
 */
?>
<!DOCTYPE html>
<?php
$email = '';
$rationale = '';
$status = array();

// Get the values from the REQUEST parameters
foreach ($_REQUEST as $name => $value) {
	if ($name == 'email') {
		$email = $value; // XXX do stripslashes() here and below?
	} elseif ($name == 'rationale') {
		$rationale = $value;
	} elseif ($value == 'TBW' || $value == 'WIP' || $value == 'SCS' || $value == 'none') {
		// Ignore any other values, including empty values.
		$status[$name] = $value;
	}
}

// Ensure that email and rationale were provided
if ($email == '' || !isValidEmail($email)
 || $rationale == '' || !isUTF8($rationale) || mb_strlen($rationale) > 125) {
	getMissingInfo($email, $rationale, $status);
} else {
	$body = getMailConfirmRequest($email, $rationale, $status);
	$sig = "HTML5 Status Updates\nhttp://www.whatwg.org/html5";

	$mail = new Email();
	$mail->setSubject("HTML5 Status Update");
	$mail->addRecipient('To', 'Lachlan Hunt', 'whatwg@lachy.id.au');
	$mail->setFrom("WHATWG", "whatwg@whatwg.org");
	$mail->setSignature($sig);
	$mail->setText($body);
	$mail->send();

	outputConfirmation($body, $sig);
}

function getMissingInfo($email, $rationale, $status) {
?>
	<title>Update Status Error</title>
    <p>You must provide a valid email address and rationale that is &le; 125 characters.</p>
	<form method="post" action="">
		<p><label for="email">Email: <input type="email" name="email" id="email" value="<?php echo htmlspecialchars($email); ?>"></label>
		<p><label for="rationale">Rationale: <input type="text" name="rationale" id="rationale" maxlength="125" size="70" value="<?php echo htmlspecialchars($rationale); ?>"></label>
		<p><input type="submit" value="save">
<?php
	foreach ($status as $name => $value) {
		echo "		<input type=\"hidden\" name=\"" . htmlspecialchars($name) . "\" value=\"" . htmlspecialchars($value) . "\">\n";
	}
?>        
    </form>
<?php
}

function getMailConfirmRequest($email, $rationale, $status) {
	$body  = "The following changes were requested by $email\n";
	$body .= "Rationale: $rationale\n\n";
	$url = 'http://status.whatwg.org/update-markers.php?email=' . urlencode($email)
	     . '&rationale=' . urlencode($rationale);

	foreach ($status as $name => $value) {
		$body .= "$name: $value\n";
		$url  .= '&'.urlencode($name).'='.urlencode($value);
	}
	
	$body .= "\nConfirm these changes:\n$url\n";
	return $body;
}

function outputConfirmation($body, $sig) {
?>
	<title>Update Status Confirmation</title>
	<p>Your changes need to be confirmed before they will be committed.
	   The following request has been sent:
	<pre><?php echo "$body\n-- \n$sig"?></pre>
<?php
}

function updateDB($email, $rationale, $status) {
?>
	<title>Update Status</title>
	<p>This feature has not been implemented yet.
<?php
}
?>