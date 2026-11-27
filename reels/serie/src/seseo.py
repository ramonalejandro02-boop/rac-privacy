import re
def seseo(t):
    """Respell for Latin American pronunciation: c+e/i -> s, z -> s (keeps accents)."""
    t=re.sub(r'c([eéiíEÉIÍ])',r's\1',t); t=re.sub(r'C([eéiíEÉIÍ])',r'S\1',t)
    return t.replace('z','s').replace('Z','S')
