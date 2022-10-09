from trade.engine import MainEngine
from trade.ui import MainWindow, create_qapp


def main():
    # 创建一个桌面应用，设置基本样式
    qapp = create_qapp()

    # 后台服务启动入口
    main_engine = MainEngine()

    # 主窗口设置
    main_window = MainWindow(main_engine)
    main_window.showMaximized()

    # 启动桌面应用
    qapp.exec()

if __name__ == "__main__":
    main()
