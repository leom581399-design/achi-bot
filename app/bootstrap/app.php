<?php
declare(strict_types=1);

require_once __DIR__ . '/../../vendor/autoload.php';

use App\Core\Application;
use App\Core\Kernel;
use App\Core\Helper\EnvHelper;

EnvHelper::load(__DIR__ . '/../../.env');

$app = Application::getInstance();

$app->singleton(Kernel::class, fn(Application $app) => new Kernel($app));

return $app;
