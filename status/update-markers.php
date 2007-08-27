<?php
header("Content-Type: text/html; charset=UTF-8");
require_once "mail-utf8.php";

/*
 * TODO:
 *
 * Twitter message: "Status Update: $rationale"
 * Required input validation:
 * - check rationale validity to prevent hackers doing bad stuff ...?
 * 
 * Finish writing the code to send appropriate emails
 * - Confirmation requests probably to Hixie
 * - Confirmed status updates to commit-watches
 * Write the confirmation system to check in updates to the DB
 */

function is_valid_email($email) {
	$pattern = "/^[a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i";
	return preg_match($pattern, $email);
}

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
	} elseif ($value != '' && ($value == 'TBW' || $value == 'WIP' || $value == 'SCS' || $value == 'none')) {
		$status[$name] = $value;
	}
}

// Ensure that email and rationale were provided
if ($email == '' || !is_valid_email($email) || $rationale == '' || mb_strlen($rationale) > 125) {
	getMissingInfo($email, $rationale, $status);
} else {
	$body = getMailConfirmRequest($email, $rationale, $status);
//	sendMail('HTML5 Status Test', 'user@example.com', $body);
	outputConfirmation($body);
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
		echo "		<input type=\"hidden\" name=\"" . htmlspecialchars($name); . "\" value=\"" . htmlspecialchars($value) . "\">\n";
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

function outputConfirmation($body) {
	$sig      = "HTML5 Status Updates\nhttp://www.w3.org/html/\nhttp://www.whatwg.org/";
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
	<p>A confirmation email has been sent.
<?php
}
?>