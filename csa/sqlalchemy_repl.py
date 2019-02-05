from django_peo.settingslocal import DATABASE_CSA, DATABASES

from sqlalchemy import create_engine, MetaData, Table, Column, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.sql import table, column, select, update, insert, delete

from csa.models import (CARRIERA_DOCENTE_FIELDS_MAP,
                        CARRIERA_FIELDS_MAP,
                        INCARICHI_FIELDS_MAP)

engine = create_engine("oracle://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}".format(**DATABASE_CSA))
metadata = MetaData()
anagrafica = Table('V_ANAGRAFICA', metadata, autoload=True, autoload_with=engine)
ruolo = Table('V_RUOLO', metadata, autoload=True, autoload_with=engine)
carriera = Table('V_CARRIERA', metadata, autoload=True, autoload_with=engine)
carriera_docente = Table('V_CARRIERA_DOCENTI', metadata, autoload=True, autoload_with=engine)
incarico = Table('V_INCARICO_DIP', metadata, autoload=True, autoload_with=engine)
# creo una sessione orm
session = Session(engine)

# repliche
engine_repl = create_engine("mysql://{USER}:{PASSWORD}@{HOST}/{NAME}".format(**DATABASES['default']))
metadata_repl = MetaData()
anagrafica_repl = Table('V_ANAGRAFICA', metadata_repl, autoload=True, autoload_with=engine_repl)
ruolo_repl = Table('V_RUOLO', metadata_repl, autoload=True, autoload_with=engine_repl)
carriera_repl = Table('V_CARRIERA', metadata_repl, autoload=True, autoload_with=engine_repl)
carriera_docente_repl = Table('V_CARRIERA_DOCENTI', metadata_repl, autoload=True, autoload_with=engine_repl)
incarico_repl = Table('V_INCARICO_DIP', metadata_repl, autoload=True, autoload_with=engine_repl)
session_repl = Session(engine_repl)


def run_anagrafica_repl():
    anagrafica_insert = insert(anagrafica_repl)
    anagrafica_update = update(anagrafica_repl)
    # for every entry in csa, find if it exists in repl and update, otherwise insert
    for i in session.query(anagrafica).all():
        #print(i._asdict())
        data = {'nome': i.nome,
                'cognome': i.cognome,
                'matricola': i.matricola,
                'email': i.email,
                'cod_fis': i.cod_fis}
        dip = session_repl.query(anagrafica_repl).filter_by(matricola=i.matricola).first()
        if dip:
            # update
            # print('updating {}'.format(data))
            anagrafica_update.values(**data)
            continue
        else:
            # print('inserting {}'.format(data))    
            # if not dip create it
            ins = anagrafica_insert.values(**data)
        session_repl.execute(ins)

def run_ruolo_repl():
    truncate = ruolo_repl.delete()
    session_repl.execute(truncate)
    
    ruolo_insert = insert(ruolo_repl)
    ruolo_update = update(ruolo_repl)
    # for every entry in csa, find if it exists in repl and update, otherwise insert
    for i in session.query(ruolo).all():
        #print(i._asdict())
        data = {'ruolo': i.ruolo,
                'comparto': i.comparto,
                'tipo_ruolo': i.tipo_ruolo,
                'descr': i.descr,
                'is_docente': i.is_docente}
        dip = session_repl.query(ruolo_repl).filter_by(ruolo=i.ruolo).first()
        if dip:
            # update
            # print('updating {}'.format(data))
            ruolo_update.values(**data)
            continue
        else:
            # print('inserting {}'.format(data))    
            # if not dip create it
            ins = ruolo_insert.values(**data)
        session_repl.execute(ins)

def run_carriera_repl():
    # clean all
    truncate = carriera_repl.delete()
    session_repl.execute(truncate)
    # session_repl.commit()

    carriera_insert = insert(carriera_repl)
    carriera_update = update(carriera_repl)
    # for every entry in csa, find if it exists in repl and update, otherwise insert
    for i in session.query(carriera).all():
        #print(i._asdict())
        data = {CARRIERA_FIELDS_MAP[k]:getattr(i, v) for k,v in CARRIERA_FIELDS_MAP.items()}
        data['matricola'] = i.matricola
        # evito duplicati
        dip = session_repl.query(carriera_repl).filter_by(**data).first()
        if dip:
            # update
            # print('updating {}'.format(data))
            # carriera_update.values(**data)
            continue
        # else:
        print('inserting carriera {}'.format(i.matricola))    
            # if not dip create it
        ins = carriera_insert.values(**data)
        session_repl.execute(ins)

def run_carriera_docenti_repl():
    # clean all
    truncate = carriera_docente_repl.delete()
    session_repl.execute(truncate)
    # session_repl.commit()

    carriera_docente_insert = insert(carriera_docente_repl)
    carriera_docente_update = update(carriera_docente_repl)
    # for every entry in csa, find if it exists in repl and update, otherwise insert
    for i in session.query(carriera_docente).all():
        #print(i._asdict())
        data = {CARRIERA_DOCENTE_FIELDS_MAP[k]:getattr(i, v) for k,v in CARRIERA_DOCENTE_FIELDS_MAP.items()}
        data['matricola'] = i.matricola
        # evito duplicati
        dip = session_repl.query(carriera_docente_repl).filter_by(**data).first()
        if dip:
            # update
            # print('updating {}'.format(data))
            # carriera_update.values(**data)
            continue
        # else:
        print('inserting carriera_docente {}'.format(i.matricola))
            # if not dip create it
        ins = carriera_docente_insert.values(**data)
        session_repl.execute(ins)

def run_incarico_repl():
    # clean all
    truncate = incarico_repl.delete()
    session_repl.execute(truncate)
    # session_repl.commit()
    
    incarico_insert = insert(incarico_repl)
    incarico_update = update(incarico_repl)
    # for every entry in csa, find if it exists in repl and update, otherwise insert
    for i in session.query(incarico).all():
        #print(i._asdict())
        data = {INCARICHI_FIELDS_MAP[k]:getattr(i, v) for k,v in INCARICHI_FIELDS_MAP.items()}
        data['matricola'] = i.matricola
        dip = session_repl.query(incarico_repl).filter_by(**data).first()
        if dip:
            # update
            # print('updating {}'.format(data))
            # incarico_update.values(**data)
            continue
        # else:
        # print('inserting {}'.format(data))    
            # if not dip create it
        ins = incarico_insert.values(**data)
        session_repl.execute(ins)

# execute replica
run_anagrafica_repl()
run_ruolo_repl()
run_carriera_repl()
run_carriera_docenti_repl()
run_incarico_repl()
session_repl.commit()
