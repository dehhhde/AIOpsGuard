@echo off
echo =====================================
echo Target Application - AIOps Test App
echo =====================================
echo.

REM 检查 Java 版本
java -version
echo.

REM 编译项目
echo [1/2] Building project...
call mvn clean package -DskipTests
if %ERRORLEVEL% NEQ 0 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo [2/2] Starting application...
echo.

REM 运行应用
java -Xms512m -Xmx1024m -jar target\target-app-1.0.0.jar

pause
