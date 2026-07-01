import json,os,re,threading,time,urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
from bs4 import BeautifulSoup
from flask import Flask,jsonify,request
from flask_cors import CORS

app=Flask(__name__)
CORS(app)
URL="https://pckj28.com"
H={"User-Agent":"Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36"}
db=[]
lock=threading.Lock()

def ft():
    r=requests.get(URL,headers=H,timeout=10,verify=False)
    r.encoding="utf-8"
    soup=BeautifulSoup(r.text,"html.parser")
    rows=soup.select("div.result-tr")
    recs=[]
    for row in rows:
        sp=row.find_all("span")
        if len(sp)<3:continue
        p=sp[0].text.strip()
        t=sp[1].text.strip()
        fx=sp[2].get_text().strip()
        m=re.match(r"(\d)\+(\d)\+(\d)=(\d{1,2})",fx)
        if m:
            s=int(m.group(4))
            recs.append({"p":p,"t":t,"n1":int(m.group(1)),"n2":int(m.group(2)),"n3":int(m.group(3)),"s":s,"bs":"大" if s>=14 else "小","oe":"单" if s%2==1 else "双"})
    return recs

def predict(d):
    n=len(d)
    b=sum(1 for r in d if r["bs"]=="大")
    s=n-b
    o=sum(1 for r in d if r["oe"]=="单")
    e=n-o
    lb=d[0]["bs"]
    lo=d[0]["oe"]
    bs_st=1
    oe_st=1
    for i in range(1,n):
        if d[i]["bs"]==lb:bs_st+=1
        else:break
    for i in range(1,n):
        if d[i]["oe"]==lo:oe_st+=1
        else:break
    v={"大":0,"小":0,"单":0,"双":0}
    rs=[]
    if bs_st>=3:
        rv="小" if lb=="大" else "大"
        v[rv]+=2
        rs.append("反转:"+lb+"x"+str(bs_st)+"→"+rv)
    else:
        v[lb]+=1
        rs.append("延续:"+lb+"x"+str(bs_st))
    if oe_st>=3:
        rv="双" if lo=="单" else "单"
        v[rv]+=2
        rs.append("反转:"+lo+"x"+str(oe_st)+"→"+rv)
    else:
        v[lo]+=1
        rs.append("延续:"+lo+"x"+str(oe_st))
    v["小" if b>s else "大"]+=1
    v["双" if o>e else "单"]+=1
    rs.append("回归:大"+str(b)+"/小"+str(s))
    rs.append("回归:单"+str(o)+"/双"+str(e))
    final_bs="大" if v["大"]>v["小"] else "小"
    final_oe="单" if v["单"]>v["双"] else "双"
    return {"bs":final_bs,"oe":final_oe,"st":{"total":n,"big":b,"small":s,"odd":o,"even":e,"bigPct":round(b/n*100,1),"smallPct":round(s/n*100,1),"oddPct":round(o/n*100,1),"evenPct":round(e/n*100,1)},"sk":{"bs":lb+"x"+str(bs_st),"oe":lo+"x"+str(oe_st)},"rs":rs,"r10":d[:10]}

@app.route("/api/fetch")
def af():
    recs=ft()
    with lock:
        ep={r["p"] for r in db}
        new=0
        for r in recs:
            if r["p"] not in ep:
                db.append(r)
                ep.add(r["p"])
                new+=1
        db.sort(key=lambda x:x["p"],reverse=True)
    return jsonify({"ok":True,"new":new,"total":len(db)})

@app.route("/api/predict")
def ap():
    if not db:
        recs=ft()
        with lock:
            for r in recs:
                db.append(r)
            db.sort(key=lambda x:x["p"],reverse=True)
    return jsonify(predict(db))

@app.route("/")
def home():
    return jsonify({"status":"ok","total":len(db)})

if __name__=="__main__":
    try:
        recs=ft()
        with lock:
            for r in recs:
                db.append(r)
            db.sort(key=lambda x:x["p"],reverse=True)
    except:pass
    def auto():
        while True:
            time.sleep(180)
            try:
                recs=ft()
                with lock:
                    ep={r["p"] for r in db}
                    for r in recs:
                        if r["p"] not in ep:db.append(r)
                    db.sort(key=lambda x:x["p"],reverse=True)
            except:pass
    threading.Thread(target=auto,daemon=True).start()
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)

