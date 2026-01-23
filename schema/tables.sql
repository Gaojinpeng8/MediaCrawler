/*
 Navicat Premium Data Transfer

 Source Server         : syj1
 Source Server Type    : MySQL
 Source Server Version : 80300 (8.3.0)
 Source Host           : localhost:3306
 Source Schema         : social

 Target Server Type    : MySQL
 Target Server Version : 80300 (8.3.0)
 File Encoding         : 65001

 Date: 02/08/2024 23:31:49
*/
create database if not exists social_monitor;
use social_monitor;
/*SET NAMES utf8mb4;
set global character_set_server=utf8mb4;*/
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for content
-- ----------------------------
DROP TABLE IF EXISTS `content`;
CREATE TABLE `content` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '默认自增主键',
  `hot_id` bigint DEFAULT NULL COMMENT '帖子对应的热榜自增ID，搜索得到帖子此处为NULL',
  `content_source` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '帖子来源',
  `content_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'xhswb帖子id，ks视频id，zh回答id，统一称为帖子',
  `question_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT 'zh对应的问题id',
  `content_crawl_time` bigint NOT NULL COMMENT '帖子爬取时间',
  `content_title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '帖子标题，只有xhs有',
  `content_desc` text,
  `content_time` bigint NOT NULL COMMENT '帖子发布时间',
  `content_user_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '发帖用户id',
  `content_user_gender` int NOT NULL DEFAULT '-1' COMMENT '发帖用户性别，1为男，0为女，-1为无性别',
  `content_user_nickname` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '发帖用户昵称',
  `content_user_home` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '发帖用户主页，只有zh有',
  `content_viewd_cnt` bigint DEFAULT NULL COMMENT 'ks有视频观看数',
  `content_liked_cnt` bigint DEFAULT NULL COMMENT '帖子喜欢数/赞同数\r\n',
  `content_collected_cnt` bigint DEFAULT NULL COMMENT '帖子收藏数，zhwb无',
  `content_comment_cnt` bigint DEFAULT NULL COMMENT '帖子评论数，ks无',
  `content_shared_cnt` bigint DEFAULT NULL COMMENT '帖子分享数，zhks无',
  `content_ip` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '帖子ip，只有wb有',
  `content_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '帖子链接，ks是视频链接',
  `content_pics` text COMMENT '帖子里图片链接存储在mongoDB里的id，类似这种格式，_id,_id,_id,取出来用split隔开',
  `content_videos` text COMMENT 'mongodb存储的对应id，ks视频下载链接在mongoDB里',
  `content_emotion` varchar(255) DEFAULT NULL,
  `content_musics` text COMMENT '帖子里面的音频下载链接，主要是dy、ks等平台',
  `content_cover_url` text COMMENT '视频封面图片，dy有',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=822 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC

-- ----------------------------
-- Table structure for comment
-- ----------------------------
DROP TABLE IF EXISTS `comment`;
CREATE TABLE `comment` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '自增id',
  `content_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论的帖子id，zh可能是问题或回答，在开头增加q和a作区分',
  `comment_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论id',
  `par_comment_id` varchar(255) NOT NULL DEFAULT '0' COMMENT '父评论id，一级评论此值为0',
  `comment_crawl_time` bigint NOT NULL COMMENT '评论爬取时间',
  `comment_time` bigint NOT NULL COMMENT '评论时间',
  `comment_desc` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论内容',
  `sub_comment_cnt` int NOT NULL COMMENT '子评论数',
  `comment_liked_cnt` int DEFAULT NULL COMMENT '评论点赞数，xhs无',
  `comment_ip` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '评论ip，ks无，',
  `comment_user_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论用户id',
  `comment_user_nickname` varchar(255) NOT NULL COMMENT '评论用户名',
  `comment_user_gender` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '-1' COMMENT '评论用户性别，1为男，0为女，-1为无性别',
  `comment_user_home` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '评论用户主页，xhsks无',
  `comment_source` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论来源',
  `comment_pics` text COMMENT 'comment中间的pics链接，json格式',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=4702 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC


-- ----------------------------
-- Table structure for NLP extract_info
-- ----------------------------
drop table if exists `extract_info`;
CREATE TABLE `extract_info` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `content_id` bigint NOT NULL COMMENT '帖子iID或者',
  `content_type` int NOT NULL COMMENT '1.热榜;2.帖子;3.评论',
  `content_source` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '来源平台',
  `city_entity` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '城市实体,逗号隔开',
  `industry_entity` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '行业实体,逗号隔开',
  `figure_entity` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '公司实体,逗号隔开',
  `three_emo` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '三分类情感',
  `six_emo` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '六分类情感',
  `summary` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '摘要, 评论摘要或者帖子摘要',
  `clustering` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '文本聚类结果, 评论没有聚类结果',
  `view` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '抽取的观点',
  `hot_topics` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '热点主题分类',
  `domain` varchar(255) DEFAULT NULL COMMENT '新闻所属的领域',
  `posts_topics` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '帖子主题分类',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=5523 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC


-- ----------------------------
-- Table structure for monitor plan
-- ----------------------------
drop table if exists `monitor_group`;
CREATE TABLE `monitor_group` (
  `group_id` int NOT NULL AUTO_INCREMENT COMMENT '监控组ID',
  `group_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '监控组名称',
  PRIMARY KEY (`group_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC

drop table if exists `monitor_plan`;
CREATE TABLE `monitor_plan` (
  `plan_id` bigint NOT NULL AUTO_INCREMENT COMMENT '方案ID',
  `group_id` int DEFAULT NULL COMMENT '监控组ID',
  `group_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '监控组名称',
  `plan_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '方案名称',
  `keywords` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '关键词, 存入列表字符串的形式['','']',
  `ignore_keywords` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '忽略关键词, 存入列表字符串的形式['','']',
  `platform` varchar(255) DEFAULT 'all' COMMENT '平台: all, xhs,ks,zh,wb',
  `emotion` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '情感: all, positive, negative, neutral',
  `topics` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '话题, 存入列表字符串的形式['','']',
  `domain` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '领域:all, ...',
  `monitor_time_interval` int NOT NULL COMMENT '监控时间间隔，单位小时',
  `last_update_time` bigint DEFAULT NULL COMMENT '最后更新的时间戳',
  `last_analysis_time` bigint DEFAULT NULL COMMENT '最后一侧分析时间',
  `monitor_time_range` bigint NOT NULL COMMENT '监控范围,检测的数据是过去多久的数据, 时间戳',
  `warning_interval` int NOT NULL COMMENT '预警时间间隔,设置多久做一个事件的传播分析，单位小时',
  `warning_rate` double NOT NULL COMMENT '预警阈值, 社交网络传播阈值',
  `describe` varchar(512) NOT NULL COMMENT '检测方案的描述',
  `status` tinyint(1) DEFAULT '1' COMMENT '这个监测方案是否运行，true代表运行，false代表不运行',
  `create_time` bigint NOT NULL DEFAULT ((unix_timestamp(now(3)) * 1000)) COMMENT '方案创建的时间',
  PRIMARY KEY (`plan_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=931 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC


drop table if exists `user`;
create table `user`(
    `user_id`   int auto_increment comment '用户id'
        primary key,
    `user_name` varchar(255) not null comment '用户名',
    `pass_word` varchar(255) null comment '用户密码'
);

SET FOREIGN_KEY_CHECKS = 1;

drop table if exists `plan_content`;
CREATE TABLE `plan_content` (
  `relation_id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `content_type` int NOT NULL DEFAULT '2' COMMENT '1.热榜;2.帖子;3.评论',
  `content_id` bigint NOT NULL COMMENT '帖子ID或者热榜ID，或者评论ID（ID主键）',
  `status` int DEFAULT '1' COMMENT '0: 不进行更新, 1: 进行更新',
  `plan_id` bigint NOT NULL COMMENT '检测方案的ID',
  `keyword_id` varchar(255) DEFAULT NULL COMMENT '搜索的到的帖子对应的“搜索关键词对应的ID-具体关键词”，这里的ID是主键，如果没有-代表没有具体的关键词。',
  PRIMARY KEY (`relation_id`),
  KEY `plan_content_ibfk_1` (`plan_id`),
  CONSTRAINT `plan_content_ibfk_1` FOREIGN KEY (`plan_id`) REFERENCES `monitor_plan` (`plan_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7028 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='方案帖子关联表'

-- 热度历史表
drop table if exists `history`;
CREATE TABLE `history` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `search_keyword_id` bigint NOT NULL COMMENT '搜索关键词id',
  `search_keyword` varchar(255) DEFAULT NULL COMMENT '具体的搜索关键词',
  `total_posts` int NOT NULL DEFAULT 0 COMMENT '该关键词下面帖子的总数量',
  `total_views` bigint NOT NULL DEFAULT 0 COMMENT '帖子的总浏览量',
  `total_likes` bigint NOT NULL DEFAULT 0 COMMENT '总点赞量',
  `avg_views` bigint NOT NULL DEFAULT 0 COMMENT '平均浏览量',
  `avg_likes` bigint NOT NULL DEFAULT 0 COMMENT '平均点赞量',
  `positive_comments` int NOT NULL DEFAULT 0 COMMENT '正向评论的数量',
  `negative_comments` int NOT NULL DEFAULT 0 COMMENT '负向评论的数量',
  `neutral_comments` int NOT NULL DEFAULT 0 COMMENT '中性评论的数量',
  `positive_posts` int NOT NULL DEFAULT 0 COMMENT '正向帖子的数量',
  `negative_posts` int NOT NULL DEFAULT 0 COMMENT '负向帖子的数量',
  `neutral_posts` int NOT NULL DEFAULT 0 COMMENT '中性帖子的数量',
  `hottest_post_id` varchar(255) DEFAULT NULL COMMENT '热度最高的帖子id',
  `hottest_comment_id` varchar(255) DEFAULT NULL COMMENT '热度最高的评论id',
  `search_time` bigint NOT NULL COMMENT '搜索时间',
  `create_time` bigint NOT NULL DEFAULT ((unix_timestamp(now(3)) * 1000)) COMMENT '记录创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_search_keyword_id` (`search_keyword_id`),
  KEY `idx_search_time` (`search_time`),
  KEY `idx_keyword_time` (`search_keyword_id`, `search_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='热度历史记录表'