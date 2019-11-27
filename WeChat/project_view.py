# -*- coding: utf-8 -*-
# @Time : 2019/11/20
# @Author : zhang
# @Site :
# @File : project_view.py
# @Software: PyCharm
import datetime
from copy import deepcopy
from json import loads

from flask import jsonify

from utils import status_code
from utils.BaseView import BaseView


class WechatProBase(BaseView):

    def __init__(self):
        super(WechatProBase, self).__init__()

    def administrator(self):
        return self.views()

    def admin(self):
        return self.views()

    def views(self):
        pass


class WechatProQuery(WechatProBase):

    def __init__(self):
        super(WechatProQuery, self).__init__()

    def admin(self):
        self.ids = self.get_project_ids()
        return self.views()

    def get_total_query(self, query_sql):
        result = self._db.query(query_sql)
        total = self._db.query(self.get_total_row)
        return result, total

    def main_list_query(self):
        """
        首页和列表页面搜索
        :return:
        """
        query_sql = r"""
            select SQL_CALC_FOUND_ROWS t1.id, t1.name, t1.address, t1.`status`, t1.type, t1.gamount, t1.starttime, t1.endtime, t1.guarantype,t1.wagepercent, t2.name as bank, t1.createtime  from tb_project as t1
            left join tb_bank as t2 on t1.bank = t2.id
        """
        where_sql_list = []
        if self.ids != None:
            if self.ids == []:
                self.ids = [0, ]
            where_sql_list.append(r""" t1.ID in ({}) """.format(self.to_sql_where_id()))
        if self.args.get('name', '') != '':
            where_sql_list.append(r""" CONCAT(IFNULL(t1.name,'')) LIKE '%{}%' """.format(self.args.get('name')))
        if int(self.args.get('type', '0')) != 0:
            where_sql_list.append(r""" t1.type={} """.format(self.args.get('type')))
        if self.args.get('status') != '' and self.args.get('status') == 'false':
            where_sql_list.append(r""" t1.status>1 """)
        else:
            if int(self.args.get('status', '0')) != 0:
                where_sql_list.append(r""" t1.status={} """.format(self.args.get('status')))
        if int(self.args.get('pid', '0')) != 0:
            where_sql_list.append(r""" t1.pid={} """.format(self.args.get('pid')))
        if int(self.args.get('cid', '0')) != 0:
            where_sql_list.append(r""" t1.cid={} """.format(self.args.get('cid')))
        if int(self.args.get('did', '0')) != 0:
            where_sql_list.append(r""" t1.did={} """.format(self.args.get('did')))
        if self.args.get('time', '') != '':
            where_sql_list.append(r""" t1.starttime > '{}' """.format(self.args.get('time')))
        where_sql = ''
        if where_sql_list:
            where_sql += ' where '
            where_sql += ' and '.join(where_sql_list)
        page = int(self.args.get('page', '1'))
        limit_sql = r""" limit {},{} """.format((page - 1) * 10, 10)
        total_query_sql = query_sql + where_sql + limit_sql
        result, total = self.get_total_query(total_query_sql)
        alarm = 0
        for item in result:
            if item['starttime'] is not None and item['starttime'] != '':
                item['starttime'] = self.time_to_str(item['starttime'])
            if item['endtime'] is not None and item['endtime'] != '':
                item['endtime'] = self.time_to_str(item['endtime'])
            if item['status'] > 1:
                alarm += 1
        self.success['project'] = result
        self.success['total'] = total[0]['total_row']
        self.success['alarm'] = alarm
        return self.success

    def calc_month(self, nowtime, oldtime):
        nowyear = nowtime.year
        oldyear = oldtime.year
        nowmonth = nowtime.month
        oldmonth = oldtime.month
        return (nowyear - oldyear) * 12 + (nowmonth - oldmonth)

    def formatter_subcompany(self, subcompany):
        subcompany_list = []
        if subcompany:
            for item in subcompany:
                temp_id = item.get('ID', None)
                if temp_id is None:
                    continue
                query_company_sql = r"""select ID,Name, HasBadRecord from tb_company where id={};""".format(
                    int(item.get('ID')))
                company_result = self._db.query(query_company_sql)
                if not company_result:
                    continue
                item['CompanyName'] = company_result[0]['Name']
                item['Status'] = 1 if int(company_result[0]['HasBadRecord']) > 1 else 0
                subcompany_list.append(item)
        return subcompany_list

    def one_project_query(self):
        if self.args_is_null('id'):
            return jsonify(status_code.CONTENT_IS_NULL)
        query_sql = r"""select t1.*,t7.Name as BankName,t2.Name as PID_Name,t3.Name as CID_Name,t4.Name as DID_Name,
                t5.Name as BuildName, t6.Name as ConsName, t5.HasBadRecord as BuildStatus, t6.HasBadRecord as ConsStatus
                from tb_project as t1
                LEFT JOIN tb_area as t2 on t1.PID = t2.ID
                LEFT JOIN tb_area as t3 on t1.CID = t3.ID
                LEFT JOIN tb_area as t4 on t1.DID = t4.ID
                LEFT JOIN tb_company as t5 on t5.id = t1.Build
                LEFT JOIN tb_company as t6 on t6.id = t1.Cons
                left join tb_bank as t7 on t7.id = t1.bank
                where t1.id={}""".format(self.args.get('id'))
        result = self._db.query(query_sql)[0]

        # 格式化分包企业
        subcompany = loads(result['SubCompany'])
        subcompany_list = self.formatter_subcompany(subcompany)
        result['SubCompany'] = subcompany_list
        result['BuildStatus'] = 1 if int(result['BuildStatus']) > 1 else 0
        result['ConsStatus'] = 1 if int(result['ConsStatus']) > 1 else 0

        if result.get('PrinPical', 'null') != 'null':
            result['PrinPical'] = loads(result['PrinPical'])
        # for i in ('ConsManager', 'OwnerManager'):
        #     result[i] = loads(result[i])
        progress_sql = r"""select ID,ProjectID,UploadTime,year,month from tb_progress where ProjectID={} 
                            order by year,month""".format(self.args.get('id'))
        query_sql = r"""select count(id) as persons from tb_laborinfo where ProjectID = {}""".format(self.args['id'])
        persons = self._db.query(query_sql)[0]
        result['Persons'] = persons['persons']
        result['NowTime'] = self.calc_month(datetime.datetime.now(), result['StartTime'])
        progress_result = self._db.query(progress_sql)
        for x in ('PID', 'CID', 'DID'):
            if result[x] is None:
                result[x] = ''
            if result[x + '_Name'] is None:
                result[x + '_Name'] = ''
        All_year_month = self.create_all_month(result['StartTime'], result['EndTime'])
        for i in ('StartTime', 'EndTime'):
            result[i] = result[i].strftime("%Y-%m-%d")
        # if result['Duration'] != None and result['Duration'] != '':
        #     result['Duration'] = result['Duration'].strftime("%Y-%m-%d")
        now_time = datetime.datetime.now()
        self.success['project'] = result
        self.success['all_year'] = list(All_year_month.keys())
        self.success['progress'] = []
        if progress_result:
            total = len(progress_result)
            for pindex, gress in enumerate(progress_result):
                temp_year = int(gress['year'])
                temp_month = int(gress['month'])
                for index, item in enumerate(All_year_month[str(temp_year)]):
                    if item['month'] == temp_month:
                        All_year_month[str(temp_year)][index]['is_input'] = 1
                        All_year_month[str(temp_year)][index]['id'] = gress['ID']
                    if temp_year == now_time.year and item['month'] == now_time.month:
                        All_year_month[str(temp_year)][index]['is_now_month'] = 1
                    if pindex == total - 1 and item['month'] == temp_month:
                        All_year_month[str(temp_year)][index]['is_current'] = 1
                gress['Year'] = temp_year
                gress['Month'] = temp_month
                gress['UploadTime'] = gress['UploadTime'].strftime("%Y-%m-%d")
            self.success['progress'] = self.get_default_progress(progress_result[-1]['ID'])
        self.success['year_month_info'] = All_year_month
        return self.success

    def get_temp(self, i):
        return {
            'month': i,
            'id': 0,
            'is_input': 0,
            'is_now_month': 0,
            'is_current': 0,
        }

    def create_all_month(self, start_time, end_time):
        start_year, end_year = start_time.year, end_time.year
        start_month, end_month = start_time.month, end_time.month
        all_month = {}
        if start_year == end_year:
            all_month[str(start_year)] = []
            for i in range(start_month, end_month + 1):
                temp = self.get_temp(i)
                all_month[str(start_year)].append(temp)
        else:
            for temp_year in range(start_year, end_year + 1):
                all_month[str(temp_year)] = []
                if temp_year == start_year:
                    for i in range(start_month, 13):
                        temp = self.get_temp(i)
                        all_month[str(temp_year)].append(temp)
                elif temp_year == end_year:
                    for i in range(1, end_month + 1):
                        temp = self.get_temp(i)
                        all_month[str(temp_year)].append(temp)
                else:
                    for i in range(1, 13):
                        temp = self.get_temp(i)
                        all_month[str(temp_year)].append(temp)
        return all_month

    def formatter_person(self, persons):
        back_data = []
        for person in persons:
            labor_id = None
            if 'ID' in person.keys():
                labor_id = person['ID']
            if 'id' in person.keys():
                labor_id = person['id']
            if labor_id == None:
                continue
            else:
                query_sql = r"""select t1.id, t1.name, t1.avatar, t1.entrydate as time, t1.phone, t2.ClassName as class from tb_laborinfo as t1 
                                left join tb_class as t2 on t2.ID = t1.ClassID
                                where t1.id = {};""".format(labor_id)
                result = self._db.query(query_sql)
                if not result:
                    continue
                if result[0]['name'] == '' or result[0]['name'] is None:
                    continue
                if result[0]['time'] is not None and result[0]['time'] != '':
                    person['time'] = self.time_to_str(result[0]['time'])
                for key in ('avatar', 'name', 'phone', 'class'):
                    person[key] = result[0].get(key, '')
            back_data.append(deepcopy(person))
        return back_data

    def get_default_progress(self, progressid):
        query_sql = r"""select * from tb_progress where id = {}""".format(progressid)
        result = self._db.query(query_sql)[0]
        result['Person'] = self.formatter_person(loads(result['Person']))
        query_all_pics = r"""select * from tb_pics where progressid={} and ptype=1 
                        and type>0;""".format(progressid)
        pics_result = self._db.query(query_all_pics)
        group_list = ['Progress', 'Contract', 'RealName', 'Attend', 'Wage', 'Rights',
                      'Lwages', 'LAB', 'PAB', 'Arrears', 'LPayCert']
        for i in group_list:
            temp = i + '_list'
            result[temp] = []
        for item in pics_result:
            temp_key = group_list[int(item['Type']) - 1] + '_list'
            result[temp_key].append(item)
        result['UploadTime'] = result['UploadTime'].strftime("%Y-%m-%d")
        return result

    def views(self):
        if int(self.args.get('id', '0')) == 0:
            success = self.main_list_query()
        else:
            success = self.one_project_query()

        return self.make_response(success)