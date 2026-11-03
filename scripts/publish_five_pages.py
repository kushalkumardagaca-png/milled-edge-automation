"""Publish the five approved MILLED EDGE pages and then delete only their legacy records.

Safety: the exact trigger phrase must be present. All legacy page IDs/paths are
preflighted; clean replacement URLs must be live and verified before any old
page is permanently deleted. Unexpected slugs cause an abort, not a suffix.
"""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from googleapiclient.errors import HttpError
from blogger_client import get_blog_by_url, get_blogger_service, load_site_config

ROOT = Path(__file__).resolve().parents[1]
TRIGGER = ROOT/'trigger/publish-five-pages.txt'
MANIFEST = ROOT/'publish/manifest.json'
CONFIRM = 'PUBLISH: MILLED EDGE FIVE PAGES AND DELETE THEIR LEGACY RECORDS'
REPORT = ROOT/'reports/publish-five-pages-report.json'


def now(): return datetime.now(timezone.utc).isoformat()
def page_path(page): return urlparse(page.get('url','')).path
def save(report):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f'Report saved: {REPORT}', flush=True)
def list_pages(service, blog_id):
    out=[]
    req=service.pages().list(blogId=blog_id, maxResults=500, view='ADMIN')
    while req is not None:
        res=req.execute()
        out.extend(res.get('items',[]))
        req=service.pages().list_next(req,res)
    return out
def get_page(service, blog_id, page_id):
    try: return service.pages().get(blogId=blog_id,pageId=str(page_id),view='ADMIN').execute()
    except HttpError as e:
        if getattr(e.resp,'status',None)==404: return None
        raise
def delete_new_draft(service, blog_id, page_id):
    try: service.pages().delete(blogId=blog_id,pageId=str(page_id),useTrash=False).execute()
    except Exception as e: print(f'Cleanup warning for draft {page_id}: {e}',flush=True)

def main():
    if not TRIGGER.exists() or TRIGGER.read_text(encoding='utf-8').strip()!=CONFIRM:
        print('Inactive trigger; nothing published or deleted.',flush=True); return
    cfg=json.loads(MANIFEST.read_text(encoding='utf-8'))
    config=load_site_config()
    service=get_blogger_service()
    blog=get_blog_by_url(service,config['blog_url'])
    blog_id=str(blog['id'])
    if blog_id!=str(cfg['blog_id']) or blog_id!=str(config.get('expected_blog_id')):
        raise RuntimeError(f'Blog ID mismatch; expected {cfg["blog_id"]}, got {blog_id}')
    if blog.get('url','').rstrip('/')!=cfg['blog_url'].rstrip('/'):
        raise RuntimeError('Blog URL mismatch; aborting.')
    report={'mode':'publish-five-pages','started_at_utc':now(),'blog':{'id':blog_id,'url':blog.get('url')},'pages':[],'legacy_deleted':[],'errors':[]}
    created_drafts=[]
    try:
        current=list_pages(service,blog_id)
        by_path={page_path(p):p for p in current if p.get('url')}
        # Verify all legacy records before any publication/deletion.
        for item in cfg['pages']:
            old=item['legacy_page']
            page=get_page(service,blog_id,old['id'])
            if page is None:
                continue  # Safe on a retry after a prior successful publication/deletion.
            if page_path(page)!=old['path'] or (page.get('title','').strip().casefold()!=old['title'].strip().casefold()):
                raise RuntimeError(f'Legacy preflight mismatch for {item["display_title"]}: {page.get("title")} {page.get("url")}')
        # Create or adopt all five replacement pages as drafts, checking exact slugs.
        prepared=[]
        for item in cfg['pages']:
            expected='/p/'+item['slug']+'.html'
            page=by_path.get(expected)
            content=(ROOT/item['content_file']).read_text(encoding='utf-8')
            if page:
                allowed={item['display_title'].casefold(),item['seed_title'].casefold()}
                if page.get('title','').strip().casefold() not in allowed:
                    raise RuntimeError(f'New URL already belongs to unexpected page: {page.get("title")} {page.get("url")}')
                page_id=str(page['id'])
            else:
                result=service.pages().insert(blogId=blog_id,body={'kind':'blogger#page','title':item['seed_title'],'content':content},isDraft=True).execute()
                page_id=str(result['id']); created_drafts.append(page_id)
                if page_path(result)!=expected:
                    delete_new_draft(service,blog_id,page_id)
                    raise RuntimeError(f'Blogger returned unexpected draft URL for {item["display_title"]}: {result.get("url")}; expected {expected}. Legacy pages were not deleted.')
                page=result
            # Set reader-facing display title without discarding the slug title's generated URL.
            page=service.pages().patch(blogId=blog_id,pageId=page_id,body={'title':item['display_title'],'content':content}).execute()
            if page_path(page)!=expected:
                if page_id in created_drafts: delete_new_draft(service,blog_id,page_id)
                raise RuntimeError(f'Display-title update changed the slug for {item["display_title"]}: {page.get("url")}')
            prepared.append({'id':page_id,'expected_path':expected,'display_title':item['display_title'],'legacy':item['legacy_page'],'was_live':page.get('status')=='LIVE'})
            print(f'Prepared clean URL: {item["display_title"]} {page.get("url")}',flush=True)
        # Publish and verify all five before deleting any legacy record.
        verified=[]
        for item in prepared:
            page=get_page(service,blog_id,item['id'])
            if page is None: raise RuntimeError(f'Missing replacement page {item["display_title"]}')
            if page.get('status')!='LIVE':
                service.pages().publish(blogId=blog_id,pageId=item['id']).execute()
            page=get_page(service,blog_id,item['id'])
            if page is None or page_path(page)!=item['expected_path'] or page.get('title')!=item['display_title'] or page.get('status')!='LIVE':
                raise RuntimeError(f'Live replacement verification failed for {item["display_title"]}: {page}')
            item['url']=page['url']; item['status']='LIVE'; verified.append(item)
            report['pages'].append({'id':item['id'],'title':item['display_title'],'url':item['url'],'status':'LIVE'})
            print(f'Published and verified: {item["url"]}',flush=True)
        # Only now permanently delete the exact preflighted legacy IDs.
        for item in verified:
            old=item['legacy']; page=get_page(service,blog_id,old['id'])
            if page is None:
                report['legacy_deleted'].append({'id':old['id'],'path':old['path'],'state':'already-missing'})
                continue
            if page_path(page)!=old['path'] or page.get('title','').strip().casefold()!=old['title'].strip().casefold():
                raise RuntimeError(f'Refusing legacy delete after changed record: {page.get("title")} {page.get("url")}')
            service.pages().delete(blogId=blog_id,pageId=old['id'],useTrash=False).execute()
            if get_page(service,blog_id,old['id']) is not None:
                raise RuntimeError(f'Legacy page still exists after delete: {old["id"]}')
            report['legacy_deleted'].append({'id':old['id'],'title':old['title'],'path':old['path'],'state':'permanently-deleted'})
            print(f'Permanently deleted legacy page: {old["path"]}',flush=True)
            time.sleep(0.35)
        report['finished_at_utc']=now(); report['result']='success'; save(report)
    except Exception as e:
        report['finished_at_utc']=now(); report['result']='failed'; report['errors'].append(str(e)); save(report)
        # Remove only pages that this run created and that are still drafts.
        for page_id in created_drafts:
            page=get_page(service,blog_id,page_id)
            if page and page.get('status')=='DRAFT': delete_new_draft(service,blog_id,page_id)
        raise

if __name__=='__main__': main()
