<?php
declare(strict_types=1);

require_once __DIR__ . '/vendor/autoload.php';

use App\Core\Kernel;

$app = require_once __DIR__ . '/app/bootstrap/app.php';
$app->make(Kernel::class)->run();
