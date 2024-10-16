import json, traceback
from django.http import JsonResponse
from django.shortcuts import render, redirect
import pandas as pd

from ..common.util import get_today, day_mapping, remove_splitDate
from ..config import URI, DB_PATH, DatabaseConnection
from ..sql.insert import insertCustKeyword
from ..sql.select import getSeCustKeyword_WithCust_id, \
    getArticleResultHis_WithAnchorDate_Keyword
from ..common.confirm import login_yn


def addSearchWord(request):
    print("Called addSearchWord")
    try:
        data = json.loads(request.body)
        cust_id = data.get('cust_id')
        df = getCustKeyword(cust_id)
        response_data = {'success': False, 'redirect_url': URI['DEFAULT']}
        if not df.empty:
            cust_info = df.iloc[0]
            response_data['cust_id'] = cust_info["cust_id"]
            response_data['reg_date'] = cust_info["reg_date"]
            response_data['reg_time'] = cust_info["reg_time"]
            # keyword가 None일 경우에 대한 처리 추가
            keyword_list = cust_info["keyword"].split("|") if cust_info.get("keyword") else []
            if len(keyword_list) > 0:
                response_data['keyword1'] = keyword_list[0]
            if len(keyword_list) > 1:
                response_data['keyword2'] = keyword_list[1]
            if len(keyword_list) > 2:
                response_data['keyword3'] = keyword_list[2]
        else:
            response_data['cust_id'] = cust_id
        response_data['success'] = True
        return JsonResponse(response_data)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def addSearchWordView(request):
    if login_yn(request):
        return render(request, URI['ADDSEARCHWORDVIEW'])
    else:
        return redirect(URI['DEFAULT'])

def getCustKeyword(cust_id):
    with DatabaseConnection(DB_PATH) as conn:
        df_SeCustKeyword = getSeCustKeyword_WithCust_id(
            cust_id, conn
        )
        if len(df_SeCustKeyword) == 0:
            print(f'Registered Keyword is null: [{cust_id}]')
    return df_SeCustKeyword

def getNewsList_WithDay_Keyword(day, cust_id):
    with DatabaseConnection(DB_PATH) as conn:
        df_article_his = getArticleResultHis_WithAnchorDate_Keyword(
            day, cust_id, conn
        )
        if len(df_article_his) == 0:
            print(f'Registered History is null: [{day}: {cust_id}]')
    return df_article_his


def getNewsList_WithDay_Keywords(day, keyword1, keyword2, keyword3):
    with DatabaseConnection(DB_PATH) as conn:
        df_article_his_keyword1 = getArticleResultHis_WithAnchorDate_Keyword(day, keyword1, conn)
        df_article_his_keyword2 = getArticleResultHis_WithAnchorDate_Keyword(day, keyword2, conn)
        df_article_his_keyword3 = getArticleResultHis_WithAnchorDate_Keyword(day, keyword3, conn)

        df_article_his = pd.concat([df_article_his_keyword1, df_article_his_keyword2, df_article_his_keyword3],
                                   ignore_index=True)

        if df_article_his.empty:
            print(f'Registered History is null: [{day}: {keyword1}, {keyword2}, {keyword3}]')

    return df_article_his

def saveCustKeyword(request):
    try:
        data = json.loads(request.body)  # JSON 데이터 파싱
        cust_id = data.get('cust_id')
        keyword1 = data.get('keyword1')
        keyword2 = data.get('keyword2')
        keyword3 = data.get('keyword3')

        df = getCustKeyword(cust_id)
        if not keyword1 and not keyword2 and not keyword3:
            errMessage = f"검색어를 입력해주세요."
            print(errMessage)
            return JsonResponse({'error': errMessage}, status=400)
        elif df.empty:
            with DatabaseConnection(DB_PATH) as conn:
                df_SeCustKeyword = insertCustKeyword(cust_id, keyword1, keyword2, keyword3, conn)
                # if len(df_SeCustKeyword) == 0:
                #     print(f'Save Cust Keyword: [{cust_id}] - [{keyword1}, {keyword2}, {keyword3}]')
        else:
            errMessage = f"한번 등록된 검색어는 변경이 불가합니다."
            print(errMessage)
            return JsonResponse({'error':errMessage}, status=400)
    except json.JSONDecodeError:
        errMessage="서버 오류입니다. 잠시 후 다시 시도 부탁드립니다."
        print(errMessage)
        return JsonResponse({'error':errMessage}, status=400)
    return redirect(URI['DEFAULT'])


def getMyKeyword(request):
    print("Called getMyKeyword")
    try:
        data = json.loads(request.body)
        cust_id = data.get('cust_id')
        df = getCustKeyword(cust_id)
        newdate = data.get('newdate')
        _format = '%Y%m%d'
        date = get_today(_format) if newdate is None else remove_splitDate(newdate,'.')

        response_data = {'success': False, 'date': date,'korean_day':day_mapping(date, _format)}
        if not df.empty:
            cust_info = df.iloc[0]
            keyword_list = cust_info["keyword"].split("|") if cust_info.get("keyword") else []
            if len(keyword_list) > 0:
                response_data['keyword1'] = keyword_list[0]
            if len(keyword_list) > 1:
                response_data['keyword2'] = keyword_list[1]
            if len(keyword_list) > 2:
                response_data['keyword3'] = keyword_list[2]
        else:
            response_data['cust_id'] = cust_id
        response_data['success'] = True
        return JsonResponse(response_data)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

def getTodayNewsList(request):
    print("Called getTodayNewsList")
    try:
        data = json.loads(request.body)
        keyword1 = data.get('keyword1')
        keyword2 = data.get('keyword2')
        keyword3 = data.get('keyword3')
        day = data.get('day')

        df = getNewsList_WithDay_Keywords(day, keyword1, keyword2, keyword3)

        response_data = []
        if not df.empty:
            for index, row in df.iterrows():
                article_data = {
                    'title': row['title'],
                    'link': row['link'],
                    'press': row['press'],
                    'keywords': row['keyword'],
                    'article_cnt': row['article_cnt'],
                }
                response_data.append(article_data)
        return JsonResponse(response_data, safe=False)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)