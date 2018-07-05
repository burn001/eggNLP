import eggData.PkLib as pkl
import re
from tqdm import tqdm

class SentRefiner:
    def __init__(self):
        self.p1=re.compile('\(.+?\)[가-힣]*') #괄호 내용 소거를 위한 정규식
        self.p2=re.compile('제*(\d+)') #4차산업혁명 정규식
        self.p4=re.compile('([가-힣]+)\.') #마침표 제거 정규식
        self.p3=re.compile(r'\b[가-힣a-zA-ZÀ-ÿ0-9,.\-]+\b') #문장부호 제거를 위한 정규식
    def refine_sent(self, sent):
        """
        문장을 정해진 규칙에 따라서 정제
        괄호 안에 있는 단어는 삭제
        제~차 와 같은 형식은 ~차 로 단순화
        문장부호는 일괄 제거
        """
        ret=''
        if len(sent)>1:
            ret=self.p1.sub('',sent)
            ret=self.p2.sub('\g<1>', ret)
            ret=self.p4.sub('\g<1>', ret)
            ret=' '.join(word for word in self.p3.findall(ret))
        return ret
class Docs:
    """
    structure
    doc_id: integer
    doc_title: str
    sentences: list of str -> name of key can be specified by sent_key

    """
    def __init__(self, docs_fname, sent_key='sentences'):
        self.docs_fname=docs_fname
        self.sent_refiner=SentRefiner()
        self.num_doc=0
        self.sent_key=sent_key
    def __iter__(self):
        for doc in pkl.pickle_iterator(self.docs_fname):
            yield doc
    def iter_doc(self, refine_sent=True, verbose=False):
        for i, doc in enumerate(pkl.pickle_iterator(self.docs_fname)):
            ret=''
            for sent in doc[self.sent_key]:
                if refine_sent:
                    sent=self.sent_refiner.refine_sent(sent)
                    if len(sent)>0: ret+=' '+sent
                else:
                    if len(sent)>0: ret+=' '+sent
            #진행상황 표시
            if verbose and ((i+1) % 5 ==0): print('\r'+str(i+1)+' docs processed.', flush=True, end='')
            yield ret.strip()
        if verbose: print('\r'+str(i+1)+' docs processed.', flush=True, end='\n')

    def iter_sent(self, refine_sent=True, cut_single_word=True, verbose=False):
        i=0
        for doc in pkl.pickle_iterator(self.docs_fname):
            for sent in doc[self.sent_key]:
                ret=''
                if refine_sent:
                    ret=self.sent_refiner.refine_sent(sent)
                else:
                    ret=sent
                
                #진행상황 표시
                i+=1
                if verbose and (i % 5 ==0): print('\r'+str(i)+' sentences processed.', flush=True, end='')    
                if cut_single_word and len(ret.split())<2:
                    continue
                    
                yield ret
        if verbose: print('\r'+str(i)+' sentences processed.', flush=True, end='\n')    

    def __len__(self):
        if self.num_doc==0:
            for x in pkl.pickle_iterator(self.docs_fname):
                self.num_doc+=1
        return self.num_doc
    @property
    def num_sent(self):
        ret=0
        for x in self.iter_sent(refine_sent=False):
            ret+=1
        return ret

    def find_match(self, word, match_limit=0):
        ret=[]
        num_match=0
        for doc in tqdm(pkl.pickle_iterator(self.docs_fname)):
            for sent in doc[self.sent_key]:
                if word in sent:
                    ret.append(doc)
                    num_match+=1
                    break
            if match_limit>0 and num_match==match_limit:
                break 
        return ret
    def find_first_match(self, word):
        for doc in tqdm(pkl.pickle_iterator(self.docs_fname)):
            for sent in doc[self.sent_key]:
                if word in sent:
                    return doc
        return None
class Ntokenizer:
    def __init__(self, nouns_fname=None):
        self.nouns=None
        self.nouns_fname=nouns_fname
        self.sent_refiner=SentRefiner()
        
    def load_nouns(self, nouns_fname=None):
        """미리 학습된 명사 데이터를 불러오는 함수
        parameters:
        nouns_fname: 학습된 명사 데이터 파일명
        returns
        None
        """
        if nouns_fname==None:
            if self.nouns_fname==None:
                print("Specify nouns data path.")
                return None
            else:
                nouns_fname=self.nouns_fname
        
        print("Loading trained nouns..(nouns_fname=%s)" % (self.nouns_fname))
        self.nouns=pkl.load_dumped_pickle(self.nouns_fname)
        print("Load completed.")

    def tokenize_old(self, sent, n_gram=5):
        """복합명사가 있을 때, 띄어쓰기 여부와 관계없이 가장 긴 복합명사를 추출하기 위해 최대 5개 단어를 결합하여 
        학습된 명사 사전(nouns)과 대조하고, 최대한 긴 단어와 매칭시킨 결과를 토큰으로 반환/매칭
        매칭 이후 남은 글자는 '버리고' 매칭 안된 토큰들과 합쳐서 다시 명사 사전과 대조
        """
        if self.nouns==None:
            self.load_nouns()
               
        tokens=sent.split()
        nouns=self.nouns
        
        ret=[]
        pointer=0
        while len(tokens)>0:
            composite_token=''.join([x for x in tokens[:n_gram]])
            #print(tokens)
            #find match in nouns
            L=len(composite_token)
            match=''
            if L>1:
                for i in range(0,L):
                    #print(composite_token[0:L-i])
                    if composite_token[0:L-i] in nouns:
                        match=composite_token[0:L-i]
                        break
            #append match to ret
            if match!='':
                if len(match)>1: ret.append(match)
                #calculate number of tokens consumed
                num_of_consumed_char=0
                pointer=0
                r_part_left=''
                while num_of_consumed_char<len(match):
                    num_of_consumed_char+=len(tokens[pointer])
                    pointer+=1 #move pointer accordingly
                tokens=tokens[pointer:]
                #print(match,":",r_part_left,":",pointer, tokens)
            else:
                tokens=tokens[1:]
        return ret
    
    def tokenize(self, sent, n_gram=5):
        """복합명사가 있을 때, 띄어쓰기 여부와 관계없이 가장 긴 복합명사를 추출하기 위해 최대 5개 단어를 결합하여 
        학습된 명사 사전(nouns)과 대조하고, 최대한 긴 단어와 매칭시킨 결과를 토큰으로 반환/매칭
        매칭 이후 남은 글자는 매칭 안된 토큰들과 합쳐서 다시 명사 사전과 대조
        """
        if self.nouns==None:
            self.load_nouns()
               
        tokens=sent.split()
        nouns=self.nouns
        
        ret=[]
        pointer=0
        r_part_left=''
        while len(tokens)>0:
            composite_token=''.join([x for x in tokens[:n_gram]])
            #print(tokens)
            #find match in nouns
            L=len(composite_token)
            match=''
            if L>1:
                for i in range(0,L):
                    #print(composite_token[0:L-i])
                    if composite_token[0:L-i] in nouns:
                        match=composite_token[0:L-i]
                        break
            #append match to ret
            if match!='':
                if len(match)>1: ret.append(match)
                #calculate number of tokens consumed
                num_of_consumed_char=0
                pointer=0
                r_part_left=''
                while num_of_consumed_char<len(match):
                    num_of_consumed_char+=len(tokens[pointer])
                    if num_of_consumed_char>len(match):
                        length_of_r_part_left=num_of_consumed_char-len(match)
                        r_part_left=tokens[pointer][-length_of_r_part_left:]
                    else:
                        r_part_left=''
                    pointer+=1 #move pointer accordingly
                if r_part_left!='':
                    tokens=[r_part_left]+tokens[pointer:]
                else:
                    tokens=tokens[pointer:]
                #print(match,":",r_part_left,":",pointer, tokens)
            else:
                tokens=tokens[1:]
        return ret