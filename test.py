class test1:
    def __init__(self, infos):
        self.infos = infos
        print(self.__get_sicherheitsinfos())
    
    def __get_sicherheitsinfos(self):
        return self.infos

class test2:
    def __init__(self, t2):
        self.andere_klasse = t2


T1 = test1("NICHT NORMAL")

T2 = test2(T1)


