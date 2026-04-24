from nt import pipe
from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from utils import logger

import time
import json


@AgentServer.custom_action("DailyTaskSelect")
class DailyTask(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:

        custom_order = [
            "DailySignIn",  # 每日签到
            "WildernessExplore",  # 荒野探索
            "CircusTask",  # 马戏团任务
            "DailySweep",  # 每日清扫
            "SendLizards",  # 派遣蜥蜴
            "AlchemySignboard",  # 炼金招牌
            "SkyExplore",  # 天空探索
            "RuinsExplore",  # 遗迹探索
            "WeeklyRaid",  # 每周周赛
        ]

        for key in custom_order:
            if context.tasker.stopping:
                logger.info("检测到停止任务, 开始退出agent")
                return CustomAction.RunResult(success=False)
            # 检查任务是否开启

            nodeDetail = context.get_node_data(f"{key}")
            if not nodeDetail or not nodeDetail.get("enabled", False):
                logger.info(f"任务: {key} 已禁用, 跳过该任务")
                continue

            logger.info(f"执行任务: {key}")
            IsCheck = False
            context.run_action("HallSwipeToUp")
            for i in range(3):
                image = context.tasker.controller.post_screencap().wait().get()
                if context.run_recognition(key, image).hit:
                    logger.info(f"第{i+1}轮检测到任务图标: {key}")
                    context.run_task(key)
                    IsCheck = True
                    break
                else:
                    context.run_action("HallSwipeToDown")

            if IsCheck:
                logger.info(f"完成任务: {key}")
            else:
                logger.warning(f"任务: {key} 识别失败, 跳过该任务")
            context.run_task("ReturnHall")

            time.sleep(1)

        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("WeeklyRaidFighting")
class WeeklyRaidFighting(CustomAction):
    def __init__(self):
        self.weeklyRaidList = ["永恒王座"]
        super().__init__()

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        # 每周周赛战斗
        # 1. 检测是什么副本

        if recoDetail := context.run_recognition(
            "WeeklyRaid_Check",
            context.tasker.controller.post_screencap().wait().get(),
        ):
            if recoDetail.best_result.text in self.weeklyRaidList:
                taskName = recoDetail.best_result.text
                logger.info(f"检测到周赛战斗为: {taskName}")
        else:
            logger.warning("未检测到周赛战斗")
            return CustomAction.RunResult(success=False)

        # 2. 执行战斗, 一共6~7轮
        for i in range(12):
            if MonsterReco := context.run_recognition(
                "WeeklyRaid_MonsterCheck",
                context.tasker.controller.post_screencap().wait().get(),
            ):
                if not MonsterReco.hit:
                    break
                for item in MonsterReco.all_results:
                    # 2.1 点开怪物
                    box = item.box
                    center_x, center_y = box[0] + box[2] // 2, box[1] + box[3] // 2
                    context.tasker.controller.post_click(center_x, center_y).wait()
                    time.sleep(1)
                    # 2.2 袭击怪物
                    context.run_task("WeeklyRaid_Attack")
            context.run_task("WeeklyRaid_SwipeToRight")

        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("DailyGoldCoin_BuyClayPot_Costing")
class DailyGoldCoin_BuyClayPot_Costing(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:

        argv_dict: dict = json.loads(argv.custom_action_param)
        times = int(argv_dict.get("times", 10))

        # 1. 打开商店
        context.run_task("DailyGoldCoin_OpenShop")

        # 2. 购买 ClayPot
        for i in range(times):
            if context.tasker.stopping:
                logger.info("检测到停止任务, 开始退出agent")
                return CustomAction.RunResult(success=False)
            context.run_task("DailyGoldCoin_BuyClayPot")

        # 兜底 检测最后一次是否触发土罐彩蛋
        if context.run_recognition(
            "DailyGoldCoin_BuyClayPot_Kickback",
            context.tasker.controller.post_screencap().wait().get(),
        ).hit:
            logger.info("触发了土罐彩蛋")
            context.run_task("DailyGoldCoin_BuyClayPot_Kickback_Confirm")

        context.run_task("ReturnBigMap")
        return CustomAction.RunResult(success=True)
