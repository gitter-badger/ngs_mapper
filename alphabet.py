AMBIGUITY_TABLE = {
    'A': 'A',
    'T': 'T',
    'G': 'G',
    'C': 'C',
    'N': 'N',
    'AC': 'M',
    'AG': 'R',
    'AT': 'W',
    'CG': 'S',
    'CT': 'Y',
    'GT': 'K',
    'ACG': 'V',
    'ACT': 'H',
    'AGT': 'D',
    'CGT': 'B',
    'ACGT': 'N'
}

def iupac_amb( dnalist ):
    '''
        Translates a given list of DNA nucleotides into their
        IUPAC Ambiguous counterparts

        @param dnalist - Sequence of DNA characters 

        @returns - The ambiguous base
    '''
    if not isinstance( dnalist, str ):
        dnalist = ''.join( sorted( dnalist ) )
    return AMBIGUITY_TABLE.get(dnalist)
