#!/bin/bash

# RM-01 Internet Connector - Fix "App is Damaged" Error
# 修复"应用已损坏"错误

echo "================================"
echo "RM-01 Internet Connector"
echo "Fix Damaged App Error / 修复损坏应用错误"
echo "================================"
echo ""

APP_PATH="/Applications/RM-01 Internet Connector.app"

if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: App not found at $APP_PATH"
    echo "❌ 错误：在 $APP_PATH 未找到应用"
    echo ""
    echo "Please drag the app to Applications folder first."
    echo "请先将应用拖拽到应用程序文件夹。"
    echo ""
    read -p "Press Enter to exit / 按回车键退出..."
    exit 1
fi

echo "Found app at / 找到应用于: $APP_PATH"
echo ""
echo "Removing quarantine attribute..."
echo "正在移除隔离属性..."
echo ""

# Remove quarantine attribute
sudo xattr -rd com.apple.quarantine "$APP_PATH"

if [ $? -eq 0 ]; then
    echo "✅ Success! The app should now work properly."
    echo "✅ 成功！应用现在应该可以正常工作了。"
    echo ""
    echo "You can now launch RM-01 Internet Connector from Applications."
    echo "您现在可以从应用程序文件夹启动 RM-01 Internet Connector。"
else
    echo "❌ Failed to remove quarantine attribute."
    echo "❌ 移除隔离属性失败。"
    echo ""
    echo "Please try running this command manually in Terminal:"
    echo "请在终端中手动运行此命令："
    echo ""
    echo "sudo xattr -rd com.apple.quarantine \"$APP_PATH\""
fi

echo ""
echo "================================"
read -p "Press Enter to exit / 按回车键退出..."
