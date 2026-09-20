import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3, hashlib, csv, shutil
from datetime import datetime

DB='kf7_enterprise.db'
APP='KF7 corp Enterprise'

# ---------------- Banco ----------------
def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def now(): return datetime.now().strftime('%d/%m/%Y %H:%M')
def hp(s): return hashlib.sha256(s.encode()).hexdigest()

def init_db():
    c=db(); c.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,login TEXT UNIQUE,password TEXT,role TEXT,active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS contacts(id INTEGER PRIMARY KEY,name TEXT,company TEXT,phone TEXT,email TEXT,city TEXT,status TEXT,notes TEXT,created TEXT);
    CREATE TABLE IF NOT EXISTS deals(id INTEGER PRIMARY KEY,title TEXT,contact TEXT,company TEXT,value REAL,stage TEXT,owner TEXT,prob INTEGER,due TEXT,notes TEXT,created TEXT);
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY,name TEXT,sku TEXT,category TEXT,cost REAL,price REAL,stock INTEGER,minimum INTEGER);
    CREATE TABLE IF NOT EXISTS finance(id INTEGER PRIMARY KEY,description TEXT,type TEXT,value REAL,status TEXT,due TEXT,client TEXT,created TEXT);
    CREATE TABLE IF NOT EXISTS activities(id INTEGER PRIMARY KEY,user TEXT,action TEXT,details TEXT,created TEXT);
    ''')
    if not c.execute('SELECT 1 FROM users LIMIT 1').fetchone():
        c.execute('INSERT INTO users(name,login,password,role) VALUES(?,?,?,?)',('Administrador','admin',hp('admin123'),'Administrador'))
    c.commit(); c.close()

def log(user,action,details=''):
    c=db(); c.execute('INSERT INTO activities(user,action,details,created) VALUES(?,?,?,?)',(user,action,details,now())); c.commit(); c.close()

def money(v): return 'R$ '+f'{float(v or 0):,.2f}'.replace(',','X').replace('.',',').replace('X','.')

# ---------------- Login ----------------
class Login(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(APP+' - Login'); self.geometry('470x560'); self.resizable(False,False); self.configure(bg='#0b1220'); self.build()
    def build(self):
        f=tk.Frame(self,bg='#172033',highlightthickness=1,highlightbackground='#334155'); f.place(relx=.5,rely=.5,anchor='center',width=390,height=430)
        tk.Label(f,text='KF7',fg='#38bdf8',bg='#172033',font=('Segoe UI',38,'bold')).pack(pady=(35,0))
        tk.Label(f,text='corp',fg='white',bg='#172033',font=('Segoe UI',18,'bold')).pack()
        tk.Label(f,text='ENTERPRISE CRM',fg='#64748b',bg='#172033',font=('Segoe UI',9,'bold')).pack(pady=(0,30))
        tk.Label(f,text='Usuário',fg='#cbd5e1',bg='#172033').pack(anchor='w',padx=40); self.u=ttk.Entry(f); self.u.pack(fill='x',padx=40,pady=(4,15),ipady=7)
        tk.Label(f,text='Senha',fg='#cbd5e1',bg='#172033').pack(anchor='w',padx=40); self.p=ttk.Entry(f,show='•'); self.p.pack(fill='x',padx=40,pady=(4,22),ipady=7); self.p.bind('<Return>',lambda e:self.login())
        tk.Button(f,text='ENTRAR',command=self.login,bg='#0ea5e9',fg='white',relief='flat',font=('Segoe UI',11,'bold')).pack(fill='x',padx=40,ipady=9)
        tk.Label(f,text='Acesso inicial: admin / admin123',fg='#64748b',bg='#172033').pack(pady=24)
    def login(self):
        c=db(); r=c.execute('SELECT * FROM users WHERE login=? AND password=? AND active=1',(self.u.get().strip(),hp(self.p.get()))).fetchone(); c.close()
        if not r: messagebox.showerror('Acesso negado','Usuário ou senha inválidos.'); return
        log(r['name'],'Login','Acesso ao sistema'); self.destroy(); App(r['name'],r['role']).mainloop()

# ---------------- Aplicação ----------------
class App(tk.Tk):
    NAV='#0f172a'; SIDE='#0b1220'; CARD='#172033'; BLUE='#0ea5e9'; TEXT='#e5e7eb'; MUTED='#94a3b8'
    def __init__(self,user,role):
        super().__init__(); self.user=user; self.role=role; self.title(APP+' | KF7 corp'); self.geometry('1450x850'); self.minsize(1150,700); self.configure(bg=self.NAV); self.protocol('WM_DELETE_WINDOW',self.close); self.style(); self.build(); self.dashboard()
    def style(self):
        s=ttk.Style(self); s.theme_use('clam'); s.configure('Treeview',background='#111827',foreground=self.TEXT,fieldbackground='#111827',rowheight=34); s.configure('Treeview.Heading',background='#263449',foreground='white',font=('Segoe UI',10,'bold')); s.map('Treeview',background=[('selected','#075985')]); s.configure('TEntry',fieldbackground='#0f172a',foreground='white')
    def build(self):
        top=tk.Frame(self,bg='#111827',height=65); top.pack(fill='x')
        tk.Label(top,text='KF7',fg='#38bdf8',bg='#111827',font=('Segoe UI',23,'bold')).pack(side='left',padx=(20,2)); tk.Label(top,text='corp',fg='white',bg='#111827',font=('Segoe UI',13,'bold')).pack(side='left',padx=10)
        self.search=ttk.Entry(top); self.search.insert(0,'Pesquisar...'); self.search.pack(side='left',fill='x',expand=True,padx=35,ipady=7); self.search.bind('<Return>',lambda e:self.search_all())
        tk.Label(top,text='●  '+self.user,fg='#86efac',bg='#111827',font=('Segoe UI',10,'bold')).pack(side='right',padx=22)
        self.side=tk.Frame(self,bg=self.SIDE,width=220); self.side.pack(side='left',fill='y'); self.side.pack_propagate(False); self.content=tk.Frame(self,bg=self.NAV); self.content.pack(side='left',fill='both',expand=True)
        items=[('▦','Dashboard',self.dashboard),('▥','Negócios',self.deals),('♙','Contatos',self.contacts),('▣','Empresas',self.companies),('▤','Produtos',self.products),('$','Financeiro',self.finance),('◷','Agenda',self.agenda),('▥','Relatórios',self.reports),('⚙','Configurações',self.settings)]
        for ic,n,cmd in items:
            tk.Button(self.side,text=f'  {ic}   {n}',command=cmd,anchor='w',bg=self.SIDE,fg='#cbd5e1',activebackground='#172033',activeforeground='white',relief='flat',font=('Segoe UI',11),padx=15,pady=11).pack(fill='x',padx=8,pady=2)
        tk.Label(self.side,text='KF7 CORP • ENTERPRISE',fg='#475569',bg=self.SIDE,font=('Segoe UI',8,'bold')).pack(side='bottom',pady=18)
    def clear(self):
        for w in self.content.winfo_children(): w.destroy()
    def header(self,title,sub=''):
        b=tk.Frame(self.content,bg=self.NAV); b.pack(fill='x',padx=28,pady=(20,12)); tk.Label(b,text=title,fg='white',bg=self.NAV,font=('Segoe UI',25,'bold')).pack(side='left'); tk.Label(b,text=sub,fg=self.MUTED,bg=self.NAV).pack(side='left',padx=14,pady=(10,0)); return b
    def cards(self,data):
        row=tk.Frame(self.content,bg=self.NAV); row.pack(fill='x',padx=22,pady=5)
        for title,val,ic in data:
            f=tk.Frame(row,bg=self.CARD,highlightthickness=1,highlightbackground='#27364a'); f.pack(side='left',fill='both',expand=True,padx=5)
            tk.Label(f,text=ic,fg=self.BLUE,bg=self.CARD,font=('Segoe UI',17)).pack(anchor='w',padx=15,pady=(10,0)); tk.Label(f,text=title.upper(),fg=self.MUTED,bg=self.CARD,font=('Segoe UI',8,'bold')).pack(anchor='w',padx=15,pady=(7,0)); tk.Label(f,text=val,fg='white',bg=self.CARD,font=('Segoe UI',19,'bold')).pack(anchor='w',padx=15,pady=(2,14))
    def dialog(self,title,fields,vals=None, choices=None):
        w=tk.Toplevel(self)
        w.title(title)
        w.geometry("560x650")
        w.minsize(520,520)
        w.configure(bg=self.CARD)
        w.transient(self)
        w.grab_set()

        outer=tk.Frame(w,bg=self.CARD)
        outer.pack(fill="both",expand=True)
        canvas=tk.Canvas(outer,bg=self.CARD,highlightthickness=0)
        scroll=ttk.Scrollbar(outer,orient="vertical",command=canvas.yview)
        form=tk.Frame(canvas,bg=self.CARD)
        form.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0),window=form,anchor="nw",width=515)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")

        vs={}
        choices=choices or {}
        for i,(k,label) in enumerate(fields):
            tk.Label(form,text=label,fg="#cbd5e1",bg=self.CARD,
                     font=("Segoe UI",9,"bold")).pack(anchor="w",padx=28,pady=(18 if i==0 else 9,3))
            v=tk.StringVar(value=(vals or {}).get(k,""))
            if k in choices:
                e=ttk.Combobox(form,textvariable=v,values=choices[k],state="readonly")
            else:
                e=ttk.Entry(form,textvariable=v)
            e.pack(fill="x",padx=28,ipady=7)
            vs[k]=v

        result=[None]
        def save():
            result[0]={k:v.get().strip() for k,v in vs.items()}
            w.destroy()

        buttons=tk.Frame(form,bg=self.CARD)
        buttons.pack(fill="x",padx=28,pady=25)
        tk.Button(buttons,text="CANCELAR",command=w.destroy,bg="#334155",fg="white",
                  relief="flat",font=("Segoe UI",10,"bold")).pack(side="left",fill="x",expand=True,ipady=9,padx=(0,6))
        tk.Button(buttons,text="SALVAR",command=save,bg=self.BLUE,fg="white",
                  relief="flat",font=("Segoe UI",10,"bold")).pack(side="left",fill="x",expand=True,ipady=9,padx=(6,0))
        w.bind("<Escape>",lambda e:w.destroy())
        w.bind("<Return>",lambda e:save())
        self.wait_window(w)
        return result[0]

    # Dashboard
    def dashboard(self):
        self.clear(); self.header('Dashboard','Visão geral da operação')
        c=db(); n=c.execute('SELECT COUNT(*) n FROM contacts').fetchone()['n']; nd=c.execute('SELECT COUNT(*) n FROM deals').fetchone()['n']; pipe=c.execute('SELECT COALESCE(SUM(value),0) v FROM deals').fetchone()['v']; rec=c.execute("SELECT COALESCE(SUM(value),0) v FROM finance WHERE type='Receita' AND status='Pago'").fetchone()['v']; pend=c.execute("SELECT COALESCE(SUM(value),0) v FROM finance WHERE status='Pendente'").fetchone()['v']; c.close()
        self.cards([('Clientes',str(n),'♙'),('Negócios',str(nd),'▥'),('Pipeline',money(pipe),'◆'),('Recebido',money(rec),'✓'),('A receber',money(pend),'!')])
        body=tk.Frame(self.content,bg=self.NAV); body.pack(fill='both',expand=True,padx=28,pady=20); left=tk.Frame(body,bg=self.CARD); left.pack(side='left',fill='both',expand=True,padx=(0,10)); right=tk.Frame(body,bg=self.CARD,width=360); right.pack(side='right',fill='y')
        tk.Label(left,text='FUNIL DE VENDAS',fg='white',bg=self.CARD,font=('Segoe UI',12,'bold')).pack(anchor='w',padx=20,pady=18)
        c=db();
        for st in ['Novos','Qualificação','Proposta','Negociação','Ganho','Perdido']:
            r=c.execute('SELECT COUNT(*) n,COALESCE(SUM(value),0) v FROM deals WHERE stage=?',(st,)).fetchone(); row=tk.Frame(left,bg=self.CARD); row.pack(fill='x',padx=22,pady=7); tk.Label(row,text=st,fg='#cbd5e1',bg=self.CARD,width=18,anchor='w').pack(side='left'); tk.Label(row,text=str(r['n']),fg='#94a3b8',bg=self.CARD,width=8).pack(side='left'); tk.Label(row,text=money(r['v']),fg='#38bdf8',bg=self.CARD,font=('Segoe UI',10,'bold')).pack(side='right')
        tk.Label(right,text='ATIVIDADES RECENTES',fg='white',bg=self.CARD,font=('Segoe UI',12,'bold')).pack(anchor='w',padx=20,pady=18)
        for r in c.execute('SELECT * FROM activities ORDER BY id DESC LIMIT 10'):
            tk.Label(right,text='• '+r['action'],fg='#e2e8f0',bg=self.CARD,anchor='w').pack(fill='x',padx=20,pady=2); tk.Label(right,text='  '+(r['details'] or '')+' • '+r['created'],fg='#64748b',bg=self.CARD,font=('Segoe UI',8),anchor='w').pack(fill='x',padx=20,pady=(0,5))
        c.close()

    # Kanban
    def deals(self):
        self.clear(); h=self.header('Negócios','Kanban • Pipeline comercial'); tk.Button(h,text='+ NOVO NEGÓCIO',command=self.add_deal,bg='#22c55e',fg='#052e16',relief='flat',font=('Segoe UI',10,'bold')).pack(side='right',ipadx=12,ipady=7)
        q=ttk.Entry(self.content); q.insert(0,'Filtrar negócios...'); q.pack(fill='x',padx=28,pady=(0,12),ipady=6); board=tk.Frame(self.content,bg=self.NAV); board.pack(fill='both',expand=True,padx=18)
        cols={}; colors={'Novos':'#06b6d4','Qualificação':'#38bdf8','Proposta':'#8b5cf6','Negociação':'#f59e0b','Ganho':'#84cc16','Perdido':'#ef4444'}
        for st in colors:
            f=tk.Frame(board,bg='#111827',highlightthickness=1,highlightbackground='#263449'); f.pack(side='left',fill='both',expand=True,padx=3); tk.Label(f,text=st.upper(),bg=colors[st],fg='#08111d',font=('Segoe UI',8,'bold')).pack(fill='x',ipady=7); cols[st]=f
        def load():
            term='%'+q.get().replace('Filtrar negócios...','').strip()+'%'; c=db()
            for st,f in cols.items():
                for x in f.winfo_children()[1:]: x.destroy()
                rows=c.execute('SELECT * FROM deals WHERE stage=? AND (title LIKE ? OR contact LIKE ? OR company LIKE ?)',(st,term,term,term)).fetchall(); total=sum(x['value'] or 0 for x in rows); tk.Label(f,text=f'{len(rows)} negócios • {money(total)}',fg='#64748b',bg='#111827',font=('Segoe UI',8)).pack(anchor='w',padx=8,pady=6)
                for r in rows:
                    card=tk.Frame(f,bg='white'); card.pack(fill='x',padx=6,pady=5); tk.Label(card,text=r['title'],fg='#0f172a',bg='white',font=('Segoe UI',9,'bold'),wraplength=175,anchor='w').pack(fill='x',padx=8,pady=(8,2)); tk.Label(card,text=money(r['value']),fg='#0369a1',bg='white',font=('Segoe UI',11,'bold')).pack(anchor='w',padx=8); tk.Label(card,text=f"{r['contact'] or 'Sem contato'}\n{r['owner'] or '-'} • {r['prob'] or 0}%",fg='#64748b',bg='white',font=('Segoe UI',8),anchor='w').pack(fill='x',padx=8,pady=5); tk.Button(card,text='Abrir',command=lambda i=r['id']:self.edit_deal(i),bg='#e2e8f0',relief='flat').pack(anchor='e',padx=7,pady=(0,7))
            c.close()
        q.bind('<KeyRelease>',lambda e:load()); load()
    def add_deal(self):
        f=[('title','Título'),('contact','Contato'),('company','Empresa'),('value','Valor'),('stage','Etapa'),('owner','Responsável'),('prob','Probabilidade %'),('due','Previsão'),('notes','Observações')]
        v=self.dialog('Novo negócio',f,{'stage':'Novos','owner':self.user,'prob':'20'},
                      {'stage':['Novos','Qualificação','Proposta','Negociação','Ganho','Perdido']})
        if not v:
            return
        if not v['title']:
            messagebox.showwarning('Validação','Informe o título do negócio.')
            return
        try: val=float(v['value'].replace(',','.') or 0); prob=int(v['prob'] or 0)
        except: messagebox.showerror('Erro','Valor ou probabilidade inválidos.'); return
        c=db(); c.execute('INSERT INTO deals(title,contact,company,value,stage,owner,prob,due,notes,created) VALUES(?,?,?,?,?,?,?,?,?,?)',(v['title'],v['contact'],v['company'],val,v['stage'],v['owner'],prob,v['due'],v['notes'],now())); c.commit(); c.close(); log(self.user,'Novo negócio',v['title']); self.deals()
    def edit_deal(self,i):
        c=db(); r=c.execute('SELECT * FROM deals WHERE id=?',(i,)).fetchone(); c.close(); f=[('title','Título'),('contact','Contato'),('company','Empresa'),('value','Valor'),('stage','Etapa'),('owner','Responsável'),('prob','Probabilidade %'),('due','Previsão'),('notes','Observações')]
        v=self.dialog('Editar negócio',f,{k:r[k] for k,_ in f},
                      {'stage':['Novos','Qualificação','Proposta','Negociação','Ganho','Perdido']})
        if not v:return
        try:val=float(v['value'].replace(',','.') or 0); prob=int(v['prob'] or 0)
        except:messagebox.showerror('Erro','Dados inválidos.');return
        c=db();c.execute('UPDATE deals SET title=?,contact=?,company=?,value=?,stage=?,owner=?,prob=?,due=?,notes=? WHERE id=?',(v['title'],v['contact'],v['company'],val,v['stage'],v['owner'],prob,v['due'],v['notes'],i));c.commit();c.close();log(self.user,'Negócio alterado',v['title']);self.deals()

    # Tabelas
    def table(self,title,cols,sql,add,edit,delete):
        self.clear()
        h=self.header(title)
        tk.Button(h,text="+ ADICIONAR",command=add,bg=self.BLUE,fg="white",
                  relief="flat",font=("Segoe UI",10,"bold")).pack(side="right",ipadx=12,ipady=7)
        q=ttk.Entry(self.content)
        q.insert(0,"Pesquisar...")
        q.pack(fill="x",padx=28,pady=(0,10),ipady=6)

        box=tk.Frame(self.content,bg=self.NAV)
        box.pack(fill="both",expand=True,padx=28,pady=5)
        t=ttk.Treeview(box,columns=[x[0] for x in cols],show="headings",selectmode="browse")
        for k,l,w in cols:
            t.heading(k,text=l)
            t.column(k,width=w,anchor="w")
        sy=ttk.Scrollbar(box,orient="vertical",command=t.yview)
        sx=ttk.Scrollbar(box,orient="horizontal",command=t.xview)
        t.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
        t.grid(row=0,column=0,sticky="nsew")
        sy.grid(row=0,column=1,sticky="ns")
        sx.grid(row=1,column=0,sticky="ew")
        box.grid_rowconfigure(0,weight=1)
        box.grid_columnconfigure(0,weight=1)

        def load():
            t.delete(*t.get_children())
            term="%"+q.get().replace("Pesquisar...","").strip()+"%"
            c=db()
            rows=c.execute(sql,(term,term,term)).fetchall()
            c.close()
            for r in rows:
                t.insert("", "end",iid=str(r["id"]),values=tuple(r[k] for k,_ in cols))

        def selected():
            s=t.selection()
            if not s:
                messagebox.showwarning("Seleção","Selecione um registro primeiro.")
                return None
            return s[0]

        def do_edit():
            if selected():
                edit(t)

        def do_delete():
            if selected():
                delete(t)

        actions=tk.Frame(self.content,bg=self.NAV)
        actions.pack(fill="x",padx=28,pady=(6,15))
        tk.Button(actions,text="✎ EDITAR",command=do_edit,bg="#334155",fg="white",
                  relief="flat",font=("Segoe UI",9,"bold")).pack(side="right",padx=4,ipadx=12,ipady=7)
        tk.Button(actions,text="✕ EXCLUIR",command=do_delete,bg="#7f1d1d",fg="white",
                  relief="flat",font=("Segoe UI",9,"bold")).pack(side="right",padx=4,ipadx=12,ipady=7)
        tk.Label(actions,text="Duplo clique em um registro também abre a edição.",
                 fg="#64748b",bg=self.NAV).pack(side="left")
        q.bind("<KeyRelease>",lambda e:load())
        t.bind("<Double-1>",lambda e:do_edit())
        load()

    def contacts(self):
        self.table('Contatos',[('id','ID',50),('name','Nome',220),('company','Empresa',170),('phone','Telefone',140),('email','E-mail',230),('city','Cidade',130),('status','Status',90)],'SELECT id,name,company,phone,email,city,status FROM contacts WHERE name LIKE ? OR company LIKE ? OR email LIKE ? ORDER BY id DESC',self.add_contact,self.edit_contact,self.del_contact)
    def add_contact(self):
        f=[('name','Nome'),('company','Empresa'),('phone','Telefone'),('email','E-mail'),('city','Cidade'),('status','Status'),('notes','Observações')]
        v=self.dialog('Novo contato',f,{'status':'Ativo'},{'status':['Ativo','Inativo']}) 
        if not v or not v['name']:return
        c=db();c.execute('INSERT INTO contacts(name,company,phone,email,city,status,notes,created) VALUES(?,?,?,?,?,?,?,?)',(*[v[x] for x in ['name','company','phone','email','city','status','notes']],now()));c.commit();c.close();log(self.user,'Novo contato',v['name']);self.contacts()
    def edit_contact(self,t):
        s=t.selection();
        if not s:return
        c=db();r=c.execute('SELECT * FROM contacts WHERE id=?',(s[0],)).fetchone();c.close();f=[('name','Nome'),('company','Empresa'),('phone','Telefone'),('email','E-mail'),('city','Cidade'),('status','Status'),('notes','Observações')]
        v=self.dialog('Editar contato',f,{k:r[k] for k,_ in f},{'status':['Ativo','Inativo']})
        if not v:return
        c=db();c.execute('UPDATE contacts SET name=?,company=?,phone=?,email=?,city=?,status=?,notes=? WHERE id=?',(*[v[x] for x in ['name','company','phone','email','city','status','notes']],s[0]));c.commit();c.close()
        log(self.user,'Contato alterado',v['name']); self.contacts()
    def del_contact(self,t):
        s=t.selection();
        if s and messagebox.askyesno('Confirmar','Excluir contato?'):
            c=db();c.execute('DELETE FROM contacts WHERE id=?',(s[0],));c.commit();c.close()
            log(self.user,'Contato excluído',str(s[0])); self.contacts()
    def companies(self):
        self.clear();self.header('Empresas','Visão consolidada'); box=tk.Frame(self.content,bg=self.NAV);box.pack(fill='both',expand=True,padx=28,pady=15);t=ttk.Treeview(box,columns=('company','count','city'),show='headings');
        for k,l,w in [('company','Empresa',350),('count','Contatos',120),('city','Cidade',220)]:t.heading(k,text=l);t.column(k,width=w)
        t.pack(fill='both',expand=True);c=db();
        for r in c.execute("SELECT company,COUNT(*) count,MAX(city) city FROM contacts WHERE company!='' GROUP BY company ORDER BY company"):t.insert('','end',values=(r['company'],r['count'],r['city'] or '-'))
        c.close()
    def products(self):
        self.table('Produtos',[('id','ID',50),('name','Produto',250),('sku','SKU',120),('category','Categoria',140),('price','Preço',120),('stock','Estoque',100),('minimum','Mínimo',100)],'SELECT id,name,sku,category,price,stock,minimum FROM products WHERE name LIKE ? OR sku LIKE ? OR category LIKE ? ORDER BY id DESC',self.add_product,self.edit_product,self.del_product)
    def add_product(self):
        f=[('name','Produto'),('sku','SKU'),('category','Categoria'),('cost','Custo'),('price','Preço'),('stock','Estoque'),('minimum','Mínimo')];v=self.dialog('Novo produto',f)
        if not v or not v['name']:return
        try:n=[float(v[x].replace(',','.')) if x in ('cost','price') else int(v[x] or 0) for x in ('cost','price','stock','minimum')]
        except:messagebox.showerror('Erro','Valores inválidos.');return
        c=db();c.execute('INSERT INTO products(name,sku,category,cost,price,stock,minimum) VALUES(?,?,?,?,?,?,?)',(v['name'],v['sku'],v['category'],*n));c.commit();c.close();self.products()
    def edit_product(self,t):
        s=t.selection();
        if not s:return
        c=db();r=c.execute('SELECT * FROM products WHERE id=?',(s[0],)).fetchone();c.close();f=[('name','Produto'),('sku','SKU'),('category','Categoria'),('cost','Custo'),('price','Preço'),('stock','Estoque'),('minimum','Mínimo')];v=self.dialog('Editar produto',f,{k:r[k] for k,_ in f})
        if not v:return
        try:n=[float(v[x].replace(',','.')) if x in ('cost','price') else int(v[x] or 0) for x in ('cost','price','stock','minimum')]
        except:messagebox.showerror('Erro','Valores inválidos.');return
        c=db();c.execute('UPDATE products SET name=?,sku=?,category=?,cost=?,price=?,stock=?,minimum=? WHERE id=?',(v['name'],v['sku'],v['category'],*n,s[0]));c.commit();c.close();self.products()
    def del_product(self,t):
        s=t.selection();
        if s and messagebox.askyesno('Confirmar','Excluir produto?'):c=db();c.execute('DELETE FROM products WHERE id=?',(s[0],));c.commit();c.close();self.products()
    def finance(self):
        self.table('Financeiro',[('id','ID',50),('description','Descrição',260),('type','Tipo',100),('value','Valor',120),('status','Status',120),('due','Vencimento',130),('client','Cliente',180)],'SELECT id,description,type,value,status,due,client FROM finance WHERE description LIKE ? OR client LIKE ? OR type LIKE ? ORDER BY id DESC',self.add_finance,self.edit_finance,self.del_finance)
    def add_finance(self):
        f=[('description','Descrição'),('type','Tipo: Receita/Despesa'),('value','Valor'),('status','Status: Pago/Pendente'),('due','Vencimento'),('client','Cliente')]
        v=self.dialog('Novo lançamento',f,{'status':'Pendente'},{'type':['Receita','Despesa'],'status':['Pago','Pendente']})
        if not v or not v['description']:return
        try:val=float(v['value'].replace(',','.'))
        except:messagebox.showerror('Erro','Valor inválido.');return
        c=db();c.execute('INSERT INTO finance(description,type,value,status,due,client,created) VALUES(?,?,?,?,?,?,?)',(v['description'],v['type'],val,v['status'],v['due'],v['client'],now()));c.commit();c.close();self.finance()
    def edit_finance(self,t):
        s=t.selection();
        if not s:return
        c=db();r=c.execute('SELECT * FROM finance WHERE id=?',(s[0],)).fetchone();c.close();f=[('description','Descrição'),('type','Tipo'),('value','Valor'),('status','Status'),('due','Vencimento'),('client','Cliente')]
        v=self.dialog('Editar lançamento',f,{k:r[k] for k,_ in f},{'type':['Receita','Despesa'],'status':['Pago','Pendente']})
        if not v:return
        try:val=float(v['value'].replace(',','.'))
        except:messagebox.showerror('Erro','Valor inválido.');return
        c=db();c.execute('UPDATE finance SET description=?,type=?,value=?,status=?,due=?,client=? WHERE id=?',(v['description'],v['type'],val,v['status'],v['due'],v['client'],s[0]));c.commit();c.close();self.finance()
    def del_finance(self,t):
        s=t.selection();
        if s and messagebox.askyesno('Confirmar','Excluir lançamento?'):c=db();c.execute('DELETE FROM finance WHERE id=?',(s[0],));c.commit();c.close();self.finance()
    def agenda(self):
        self.clear();self.header('Agenda','Organização comercial'); f=tk.Frame(self.content,bg=self.CARD);f.pack(fill='both',expand=True,padx=28,pady=15); tk.Label(f,text=datetime.now().strftime('%A, %d de %B de %Y'),fg='white',bg=self.CARD,font=('Segoe UI',22,'bold')).pack(pady=45); tk.Label(f,text='Compromissos podem ser vinculados aos negócios e clientes através das datas de previsão.',fg=self.MUTED,bg=self.CARD).pack()
    def reports(self):
        self.clear();self.header('Relatórios','Indicadores e exportação');c=db();pipe=c.execute('SELECT COALESCE(SUM(value),0) v FROM deals').fetchone()['v'];won=c.execute("SELECT COALESCE(SUM(value),0) v FROM deals WHERE stage='Ganho'").fetchone()['v'];pend=c.execute("SELECT COALESCE(SUM(value),0) v FROM finance WHERE status='Pendente'").fetchone()['v'];low=c.execute('SELECT COUNT(*) n FROM products WHERE stock<=minimum').fetchone()['n'];c.close();self.cards([('Pipeline',money(pipe),'◆'),('Ganho',money(won),'✓'),('A receber',money(pend),'$'),('Estoque baixo',str(low),'!')]); tk.Button(self.content,text='EXPORTAR NEGÓCIOS CSV',command=self.export,bg=self.BLUE,fg='white',relief='flat').pack(anchor='e',padx=28,pady=20)
    def export(self):
        p=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='KF7_negocios.csv');
        if not p:return
        c=db();rows=c.execute('SELECT * FROM deals ORDER BY id DESC').fetchall();c.close()
        with open(p,'w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f,delimiter=';');w.writerow(rows[0].keys() if rows else ['id','title']);[w.writerow(tuple(r)) for r in rows]
        messagebox.showinfo('Exportação','Arquivo exportado com sucesso.')
    def settings(self):
        self.clear();self.header('Configurações','Administração');self.cards([('Usuário',self.user,'♙'),('Perfil',self.role,'⚙'),('Banco','SQLite','▣')]);f=tk.Frame(self.content,bg=self.CARD);f.pack(fill='x',padx=28,pady=20);tk.Label(f,text='FERRAMENTAS',fg='white',bg=self.CARD,font=('Segoe UI',12,'bold')).pack(anchor='w',padx=20,pady=18);tk.Button(f,text='Backup do banco',command=self.backup,bg='#334155',fg='white',relief='flat').pack(fill='x',padx=20,pady=6,ipady=8);tk.Button(f,text='Verificar integridade',command=self.integrity,bg='#334155',fg='white',relief='flat').pack(fill='x',padx=20,pady=6,ipady=8);tk.Button(f,text='Histórico de auditoria',command=self.history,bg='#334155',fg='white',relief='flat').pack(fill='x',padx=20,pady=6,ipady=8)
    def backup(self):
        p=filedialog.asksaveasfilename(defaultextension='.db',filetypes=[('SQLite','*.db')],initialfile='KF7_backup.db');
        if p:shutil.copy2(DB,p);messagebox.showinfo('Backup','Backup realizado com sucesso.')
    def integrity(self):
        c=db();r=c.execute('PRAGMA integrity_check').fetchone()[0];c.close();messagebox.showinfo('Integridade',r)
    def history(self):
        self.clear();self.header('Histórico','Auditoria do sistema');box=tk.Frame(self.content,bg=self.NAV);box.pack(fill='both',expand=True,padx=28,pady=10);t=ttk.Treeview(box,columns=('date','user','action','details'),show='headings');
        for k,l,w in [('date','Data',150),('user','Usuário',150),('action','Ação',180),('details','Detalhes',500)]:t.heading(k,text=l);t.column(k,width=w)
        t.pack(fill='both',expand=True);c=db();
        for r in c.execute('SELECT created,user,action,details FROM activities ORDER BY id DESC'):t.insert('','end',values=tuple(r));
        c.close()
    def companies_dummy(self):pass
    def search_all(self):
        q=self.search.get().strip()
        if not q:
            return
        self.contacts()
        entries=[w for w in self.content.winfo_children() if isinstance(w,ttk.Entry)]
        if entries:
            entries[0].delete(0,'end')
            entries[0].insert(0,q)
            entries[0].event_generate('<KeyRelease>')
    def close(self):log(self.user,'Logout','Saída do sistema');self.destroy()

if __name__=='__main__':
    init_db(); Login().mainloop()
