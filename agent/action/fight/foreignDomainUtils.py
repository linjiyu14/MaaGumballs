from typing import TYPE_CHECKING

from maa.context import Context
from maa.custom_action import CustomAction

from utils import logger

import time

if TYPE_CHECKING:
    from action.fight.timeSpaceDomain import TSD_explore


class foreignDomainUtils:
    def __init__(self, TSD: "TSD_explore"):

        # 舰队状态roi列表
        self.fleetRoiList: dict = {
            "奥鲁维": [130, 199, 60, 51],
            "卡纳斯": [227, 200, 63, 50],
            "游荡者": [327, 200, 64, 49],
            "深渊": [425, 199, 64, 53],
        }
        self.default_fleets = ["奥鲁维", "卡纳斯", "游荡者", "深渊"]  # 默认舰队顺序
        self.TSD: "TSD_explore" = TSD
        self.check = False  # 是否从右下角开始检查
        self.direction = "Left"  # 移动方向
        self.isUp = False  # 是否上移过一次

    # 检查舰队状态，是否都是空闲
    def checkAllFleetStatus(self, context: Context) -> int:
        img = context.tasker.controller.post_screencap().wait().get()
        fleetStatus = context.run_recognition(
            "checkAllFleetStatus",
            img,
            pipeline_override={
                "checkAllFleetStatus": {
                    "recognition": "TemplateMatch",
                    "template": "fight/time_space_domain/fleetFree.png",
                    "roi": [109, 182, 397, 95],
                    "threshold": 0.8,
                }
            },
        )
        if fleetStatus.hit:
            return len(fleetStatus.filtered_results)
        else:
            return 0

    # 返回所有舰队
    def returnFleets(self, context: Context) -> bool | CustomAction.RunResult:
        while True:
            if context.tasker.stopping:
                logger.info("检测到停止任务, 开始退出agent")
                return CustomAction.RunResult(success=False)
            img = context.tasker.controller.post_screencap().wait().get()
            for key in self.TSD.fleetRoiList:
                status = context.run_recognition(
                    "TSD_checkFreeFleet",
                    img,
                    pipeline_override={
                        "TSD_checkFreeFleet": {"roi": self.TSD.fleetRoiList[key]}
                    },
                )
                if not status.hit:
                    time.sleep(1)
                    logger.info(f"正在返回{key}舰队")
                    context.run_task(
                        "TSD_ClickFleet",
                        pipeline_override={
                            "TSD_ClickFleet": {"target": self.TSD.fleetRoiList[key]}
                        },
                    )
                    context.run_task(
                        "TSD_ReturnFleet",
                        pipeline_override={
                            "TSD_checkTargetFleetFree": {
                                "roi": self.TSD.fleetRoiList[key]
                            },
                            "TSD_View": {
                                "next": [
                                    "TSD_EndExploit",
                                    "[JumpBack]TSD_WithdrawFleet",
                                    "[JumpBack]TSD_EndExplore",
                                    "[JumpBack]BackText",
                                ],
                            },
                        },
                    )
                    time.sleep(1)
                else:
                    logger.info(f"{key}舰队已返回,无需操作")
            if nums := self.checkAllFleetStatus(context) == 4:
                logger.info("所有舰队已返回")

                break
        return True

    # 关闭联盟聊天窗口
    def closeUnionMsgBox(self, context: Context) -> bool:
        img = context.tasker.controller.post_screencap().wait().get()
        opened = context.run_recognition(
            "checkUnionMsgBox",
            img,
            pipeline_override={
                "checkUnionMsgBox": {
                    "recognition": "TemplateMatch",
                    "template": "fight/time_space_domain/unionMsgOpened.png",
                    "roi": [91, 1042, 80, 80],
                    "threshold": 0.8,
                }
            },
        )
        if opened.hit:
            context.run_task("TSD_closeUnionMsgBox")
            logger.info("关闭联盟聊天窗口")
        else:
            logger.info("联盟聊天窗口未打开")
        return True

    # 检查地图边界
    def checkBoundary(self, context: Context, direction: str) -> bool:
        boundaryRoiDict: dict = {
            "LeftTop": [12, 268, 137, 147],
            "RightTop": [549, 276, 161, 147],
            "Right": [597, 272, 96, 871],
            "Left": [14, 275, 116, 766],
            "RightBottom": [590, 1052, 117, 102],
            "LeftBottom": [9, 1011, 145, 125],
        }
        img = context.tasker.controller.post_screencap().wait().get()
        boundaryList = context.run_recognition(
            "GridCheckTargetBoundary",
            img,
            pipeline_override={
                "GridCheckTargetBoundary": {
                    "recognition": "TemplateMatch",
                    "template": f"fight/time_space_domain/boundary{direction}.png",
                    "roi": boundaryRoiDict[direction],
                    "threshold": 0.92,
                }
            },
        )
        if boundaryList.hit:
            return True
        return False

    def swipeMapToLeftTop(self, context: Context):
        while True:  # 将地图移动至左上角
            if context.tasker.stopping:
                logger.info("检测到停止任务, 开始退出agent")
                return CustomAction.RunResult(success=False)
            if self.checkBoundary(context, "LeftTop"):
                break
            else:
                context.run_task("FD_SwipeMapMiddleToTopLeft")
            time.sleep(1)
        self.direction = "Right"
        self.isUp = False
        time.sleep(1)

    def swipeMapToBottomRight(self, context: Context):
        for _ in range(4):
            context.run_task("FD_SwipeMapMiddleToBottomRight")
            time.sleep(1)
        self.direction = "Left"
        self.isUp = False
        time.sleep(1)

    def swipeMap(self, context: Context) -> bool:
        if self.checkBoundary(context, self.direction):
            logger.info(f"地图{self.direction}边界")
            if self.checkBoundary(context, "LeftTop"):
                logger.info("已到达地图边界")
                if self.check:
                    self.check = False
                    return False
                else:
                    # 返回地图左上角重新检查一遍
                    self.check = True
                    self.swipeMapToBottomRight(context)
            elif not self.isUp:  # 未达到左上角，地图上移一次
                logger.info("地图上移")
                context.run_task("FD_SwipeMapToUp")
                self.direction = "Left" if self.direction == "Right" else "Right"
                self.isUp = True
                time.sleep(1)
            else:  # 已经上移过一次，按direction移动一次
                logger.info("地图移动")
                if self.direction == "Right":
                    context.run_task("FD_SwipeMapToRight")
                else:
                    context.run_task("FD_SwipeMapToLeft")
                self.isUp = False
                time.sleep(1)
        else:  # 未达到边界，地图按当前direction继续移动一次
            logger.info("地图移动")
            if self.direction == "Right":
                context.run_task("FD_SwipeMapToRight")
            else:
                context.run_task("FD_SwipeMapToLeft")
            self.isUp = False
            time.sleep(2)
        return True
