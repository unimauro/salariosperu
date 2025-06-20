#!/usr/bin/env python3
"""
Lista completa de empresas disponibles en SalariosPerú.com
Incluye empresas con tildes y caracteres especiales correctamente codificados
"""

# Lista completa de empresas (slug_url, nombre_display)
EMPRESAS_COMPLETAS = [
    # Bancos y Financieras
    ('banco-de-credito-bcp', 'Banco de Crédito BCP'),
    ('interbank', 'Interbank'),
    ('bbva-peru', 'BBVA Perú'),
    ('bbva-en-perú', 'BBVA en Perú'),
    ('scotiabank-perú', 'Scotiabank Perú'),
    ('banco-pichincha-perú', 'Banco Pichincha Perú'),
    ('banbif-banco-interamericano-de-finanzas', 'BanBif - Banco Interamericano de Finanzas'),
    ('mibanco-banco-de-la-microempresa', 'Mibanco, banco de la Microempresa'),
    ('compartamos-financiera', 'Compartamos Financiera'),
    ('financiera-credinka', 'FINANCIERA CREDINKA'),
    
    # Telecomunicaciones
    ('entel-perú', 'Entel Perú'),
    ('telefónica', 'Telefónica'),
    ('claro-perú', 'Claro Perú'),
    
    # Seguros
    ('rimac-seguros-y-reaseguros', 'Rimac Seguros y Reaseguros'),
    ('pacifico-seguros', 'Pacífico Seguros'),
    ('interseguro-compañia-de-seguros', 'Interseguro Compañía de Seguros'),
    ('la-positiva-seguros', 'La Positiva Seguros'),
    ('mapfre', 'MAPFRE'),
    
    # AFP
    ('prima-afp', 'Prima AFP'),
    ('profuturo-afp', 'Profuturo AFP'),
    ('afp-integra', 'AFP Integra'),
    
    # Retail y Consumo
    ('falabella', 'Falabella'),
    ('saga-falabella', 'Saga Falabella'),
    ('ripley-perú', 'Ripley Perú'),
    ('sodimac', 'Sodimac'),
    ('hiraoka', 'Hiraoka'),
    ('coolbox-perú', 'Coolbox Perú'),
    
    # Supermercados
    ('cencosud-scotiabank', 'Cencosud Scotiabank'),
    ('makro-peru', 'Makro Peru'),
    
    # Alimentos y Bebidas
    ('alicorp', 'Alicorp'),
    ('nestlé', 'Nestlé'),
    ('backus', 'Backus'),
    ('ajinomoto-del-perú-sa', 'Ajinomoto del Perú S.A.'),
    ('san-fernando', 'San Fernando'),
    ('grupo-aje', 'Grupo AJE'),
    ('gloria', 'Gloria'),
    ('mondelez-international', 'Mondelēz International'),
    
    # Farmacias y Cosméticos
    ('farmacias-peruanas', 'Farmacias Peruanas'),
    ('perfumerias-unidas', 'Perfumerías Unidas'),
    ('belcorp', 'Belcorp'),
    ('yanbal', 'Yanbal'),
    ('loreal', "L'Oréal"),
    ('procter-gamble', 'Procter & Gamble'),
    ('colgate-palmolive', 'Colgate-Palmolive'),
    ('kimberly-clark', 'Kimberly-Clark'),
    
    # Tecnología y Consultoría
    ('deloitte', 'Deloitte'),
    ('pwc-perú', 'PwC Perú'),
    ('ey', 'EY'),
    ('mckinsey-company', 'McKinsey & Company'),
    ('boston-consulting-group-bcg', 'Boston Consulting Group (BCG)'),
    ('accenture', 'Accenture'),
    ('everis', 'everis'),
    ('minsait', 'Minsait'),
    ('indra', 'Indra'),
    ('management-solutions', 'Management Solutions'),
    ('ntt-data-europe-latam', 'NTT DATA Europe & Latam'),
    ('stefanini-it-solutions-perú', 'Stefanini IT Solutions (Perú)'),
    ('cisco', 'Cisco'),
    
    # Petróleo y Energía
    ('repsol', 'Repsol'),
    ('enel-x', 'Enel X'),
    ('primax', 'Primax'),
    ('bp-perú', 'BP Perú'),
    
    # Minería
    ('southern-copper-corporation', 'Southern Copper Corporation'),
    ('compañia-minera-antamina', 'Compañía Minera Antamina'),
    ('minsur-sa', 'Minsur S.A.'),
    ('shougang-hierro-perú-saa', 'Shougang Hierro Perú S.A.A.'),
    ('glencore', 'Glencore'),
    ('sociedad-minera-el-brocal', 'Sociedad Minera El Brocal'),
    
    # Construcción e Inmobiliarias
    ('unacem', 'UNACEM'),
    ('cementos-pacasmayo-saa', 'Cementos Pacasmayo SAA'),
    ('graña-y-montero', 'Graña y Montero'),
    ('stracon', 'STRACON'),
    ('jjc-contratistas-generales-sa', 'JJC Contratistas Generales S.A.'),
    
    # Logística y Transporte
    ('ransa', 'Ransa'),
    ('dhl', 'DHL'),
    ('fedex', 'FedEx'),
    ('latam-airlines', 'LATAM Airlines'),
    ('sky-airline', 'SKY Airline'),
    ('talma-servicios-aeroportuarios-sa', 'Talma Servicios Aeroportuarios S.A.'),
    ('dp-world', 'DP World'),
    
    # Automotriz
    ('toyota-del-perú', 'Toyota del Perú'),
    ('divemotor', 'Divemotor'),
    ('ferreyros-sa', 'Ferreyros S.A.'),
    ('inchcape-americas', 'Inchcape Américas'),
    
    # Educación
    ('universidad-del-pacifico-pe', 'Universidad del Pacífico (PE)'),
    ('universidad-continental', 'Universidad Continental'),
    ('universidad-tecnologica-del-perú', 'Universidad Tecnológica del Perú'),
    ('corporacion-educativa-pamer', 'Corporación Educativa Pamer'),
    
    # Medios y Comunicación
    ('el-comercio', 'El Comercio'),
    ('america-television', 'América Televisión'),
    ('panamericana-television', 'Panamericana Televisión'),
    
    # Salud
    ('clinica-anglo-americana', 'Clínica Anglo Americana'),
    ('clinica-internacional', 'Clínica Internacional'),
    ('auna', 'Auna'),
    ('fresenius-medical-care', 'Fresenius Medical Care'),
    ('siemens-healthineers', 'Siemens Healthineers'),
    
    # Agricultura y Agroindustria
    ('san-miguel-industrias-pet', 'San Miguel Industrias PET'),
    ('agro-industrial-paramonga-saa', 'Agro Industrial Paramonga Saa'),
    ('viru-sa', 'Viru S.A.'),
    ('inkas-berries', "Inka's Berries"),
    
    # Startups y Fintech
    ('yape', 'Yape'),
    ('culqi', 'Culqi'),
    ('kushki', 'Kushki'),
    ('izipay', 'izipay'),
    ('jokr', 'JOKR'),
    ('rappi', 'Rappi'),
    ('pedidosya', 'PedidosYa'),
    ('despegar', 'Despegar'),
    
    # Gobierno y Organismos
    ('superintendencia-de-banca-seguros-y-administradoras-de-fondos-de-pensiones-del-perú', 'Superintendencia de Banca, Seguros y Administradoras de Fondos de Pensiones del Perú'),
    ('ministerio-de-comercio-exterior-y-turismo', 'Ministerio de Comercio Exterior y Turismo'),
    ('municipalidad-de-lima', 'Municipalidad de Lima'),
    ('bolsa-de-valores-de-lima', 'Bolsa de Valores de Lima'),
    
    # Otros Servicios
    ('prosegur', 'Prosegur'),
    ('securitas', 'Securitas'),
    ('sodexo', 'Sodexo'),
    ('manpowergroup', 'ManpowerGroup'),
    ('adecco', 'Adecco'),
    ('michael-page', 'Michael Page'),
    ('spencer-stuart', 'Spencer Stuart'),
    ('marsh', 'Marsh'),
    ('wtw', 'WTW'),
]

# Empresas de tecnología adicionales
EMPRESAS_TECH = [
    ('google', 'Google'),
    ('amazon', 'Amazon'),
    ('microsoft', 'Microsoft'),
    ('ibm', 'IBM'),
    ('oracle', 'Oracle'),
    ('salesforce', 'Salesforce'),
    ('sap', 'SAP'),
    ('vtex', 'VTEX'),
    ('mercadolibre', 'MercadoLibre'),
]

# Empresas internacionales con presencia en Perú
EMPRESAS_INTERNACIONALES = [
    ('3m', '3M'),
    ('ab-inbev', 'AB InBev'),
    ('adidas', 'adidas'),
    ('samsung-electronics', 'Samsung Electronics'),
    ('lg', 'LG'),
    ('huawei', 'Huawei'),
    ('lenovo', 'Lenovo'),
    ('hp', 'HP'),
    ('dell', 'Dell'),
]

def get_all_companies():
    """Retorna todas las empresas combinadas"""
    return EMPRESAS_COMPLETAS + EMPRESAS_TECH + EMPRESAS_INTERNACIONALES

def get_companies_by_sector(sector):
    """Retorna empresas filtradas por sector"""
    sectors = {
        'bancos': [e for e in EMPRESAS_COMPLETAS if any(word in e[1].lower() for word in ['banco', 'financiera', 'credicorp'])],
        'tecnologia': EMPRESAS_TECH,
        'retail': [e for e in EMPRESAS_COMPLETAS if any(word in e[1].lower() for word in ['falabella', 'ripley', 'sodimac', 'hiraoka'])],
        'telecomunicaciones': [e for e in EMPRESAS_COMPLETAS if any(word in e[1].lower() for word in ['entel', 'telefónica', 'claro'])],
        'seguros': [e for e in EMPRESAS_COMPLETAS if 'seguro' in e[1].lower()],
    }
    return sectors.get(sector, [])

def print_companies_summary():
    """Imprime resumen de empresas disponibles"""
    all_companies = get_all_companies()
    
    print(f"📊 RESUMEN DE EMPRESAS DISPONIBLES")
    print("=" * 50)
    print(f"Total de empresas: {len(all_companies)}")
    print(f"Empresas principales: {len(EMPRESAS_COMPLETAS)}")
    print(f"Empresas de tecnología: {len(EMPRESAS_TECH)}")
    print(f"Empresas internacionales: {len(EMPRESAS_INTERNACIONALES)}")
    
    # Contar empresas con tildes
    companies_with_tildes = [e for e in all_companies if 'ñ' in e[0] or 'ú' in e[0] or 'é' in e[0] or 'í' in e[0] or 'ó' in e[0]]
    print(f"Empresas con tildes: {len(companies_with_tildes)}")
    
    print("\n🔤 Empresas con caracteres especiales:")
    for slug, name in companies_with_tildes:
        print(f"  • {name} ({slug})")

if __name__ == "__main__":
    print_companies_summary() 