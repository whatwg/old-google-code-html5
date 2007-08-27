<?php
header("Content-Type: text/html; charset=UTF-8");
?>
<!DOCTYPE html>

<?php
$email = '';
$rationale = '';
$status = array();

foreach ($_REQUEST as $name => $value) {
	if ($name == 'email') {
		$email = $value;
	} elseif ($name == 'rationale') {
		$rationale = $value;
	} else {
		$status[$name] = $value;
	}
}

// Ensure that email and rationale were provided
if ($email == '' || $rationale == '') {
	getMissingInfo($email, $rationale, $status);
} else {
	updateDB($email, $rationale, $status);
}

function getMissingInfo($email, $rationale, $status) {
?>
	<title>Update Status Error</title>
    <p>You must provide an email address and rationale
	<form method="post" action="">
		<p><label for="email">Email: <input type="text" name="email" id="email" value="<?=$email?>"></label>
		<p><label for="rationale">Rationale: <input type="text" name="rationale" id="rationale" value="<?=$rationale?>"></label>
		<p><input type="submit" value="save">
<?php
	foreach ($status as $name => $value) {
		echo "		<input type=\"hidden\" name=\"$name\" value==\"$value\">\n";
	}
?>        
    </form>
<?php
}

function updateDB($email, $rationale, $status) {
?>
	<title>Update Status</title>
	<p>This does not yet work!  Your changes have not been saved.
<?php
}
?>