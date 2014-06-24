from imports import *

class TrimBase(common.BaseClass):
    def setUp( self ):
        super(TrimBase,self).setUp()
        # Contains sanger, miseq and 454 fastq
        self.read_dir = join( THIS, 'fixtures', 'trim_reads' )
        # Only fastq files
        self.se = [
            'sample1_F1_1979_01_01_Den2_Den2_0001_A01.fastq',
            '1121__2__TI86__2012_04_04__Den2.fastq',
        ]
        self.pe = [
            ('2952_S14_L001_R1_001_2014_06_13.fastq', '2952_S14_L001_R2_001_2014_06_13.fastq'),
        ]

        self.se = [join(self.read_dir,se) for se in self.se]
        self.pe = [[join(self.read_dir,p) for p in pe] for pe in self.pe]
        # All reads
        self.reads = self.se + self.pe

class TestTrimReadsInDir(TrimBase):
    def setUp( self ):
        super( TestTrimReadsInDir, self ).setUp()

    def _C( self, *args, **kwargs ):
        from trim_reads import trim_reads_in_dir
        return trim_reads_in_dir( *args, **kwargs )

    @attr('current')
    def test_skips_ab1( self ):
        outdir = 'filtered_reads'
        readsdir = 'reads'
        os.mkdir( readsdir )
        for r in self.se:
            shutil.copy( r, readsdir )
        for f,r in self.pe:
            shutil.copy( f, readsdir )
            shutil.copy( r, readsdir )
        with open( join(readsdir,basename(self.se[0]).replace('.fastq','.ab1')), 'w' ) as fh:
            fh.write( 'abi garbage here\n' )
        self._C( readsdir, 20, outdir )

    @attr('current')
    def test_does_not_create_empty_unpaired( self ):
        outdir = 'filtered_reads'
        readsdir = 'reads'
        os.mkdir( readsdir )
        for se in self.se:
            shutil.copy( se, readsdir )
        self._C( readsdir, 20, outdir )
        unpaired = glob( join(outdir,'unpaired*') )
        eq_( 0, len(unpaired), 'Created unpaired fastq file when it should not have' )

        shutil.rmtree(outdir)
        shutil.rmtree(readsdir)
        os.mkdir( readsdir )
        for pe1, pe2 in self.pe:
            shutil.copy( pe1, readsdir )
            shutil.copy( pe2, readsdir )
        self._C( readsdir, 20, outdir )
        unpaired = glob( join(outdir,'unpaired*') )
        if unpaired:
            ok_( os.stat( unpaired[0] ).st_size > 0, 'Created empty unpaired file when it should not have' )

    @attr('current')
    def test_runs_correctly( self ):
        # Where to put filtered reads
        outdir = 'filtered_reads'
        # Should be all the basenames with sff replaced with fastq
        expectedfiles = [basename(s) for s in self.se]
        for f,r in self.pe:
            f = basename(f)
            r = basename(r)
            expectedfiles += [f,r]
        #expectedfiles.append( 'unpaired__1__TI1__2001_01_01__Unk.fastq' )
        #expectedfiles = [f.replace('.sff','.fastq') for f in os.listdir(self.read_dir)]
        expectedfiles = sorted(expectedfiles)
        # Run
        self._C( self.read_dir, 20, outdir )

        # Grab result files
        resultfiles = sorted(os.listdir(outdir))

        # Debugging goodies
        es,rs = set(expectedfiles), set(resultfiles)
        print "In expected not in result"
        print es - rs
        print "In result not in expected"
        print rs - es

        # Make sure lists are same
        eq_( expectedfiles, resultfiles, 'Expected files({}) was not equal to Resulting files({})'.format(expectedfiles,resultfiles) )

class TestTrimRead(TrimBase):
    def setUp( self ):
        super(TestTrimRead,self).setUp()

    def _C( self, *args, **kwargs ):
        from trim_reads import trim_read
        return trim_read( *args, **kwargs )

    def check_read( self, read, r ):
        bn = basename(read)
        eq_( bn, r, 'Given outpath({}) and returned path({}) were different'.format(bn,r) )
        es = os.stat(read)
        rs = os.stat(bn)
        ok_( not samestat( es, rs ), 'Output file and inputfile are the same file' )
        ok_( 
            es.st_size > rs.st_size, 
            'Did not seem to trim the file. Output file s.st_size({}) was not smaller than input file s.st_size({})'.format(rs.st_size,es.st_size)
        )
        ok_( isdir('trim_stats'), 'Did not create trim_stats directory' )
        trimstatsfile = join( 'trim_stats', bn + '.trim_stats' )
        ok_( exists(trimstatsfile), 'Did not create trimstats file {}'.format(trimstatsfile) )

    def test_trims_se( self ):
        # Make sure output path and returned path are ==
        # Make sure output path exists
        # Make sure output file is smaller than input file
        for read in self.se:
            bn = basename(read)
            r = self._C( read, 40, bn )
            self.check_read( read, r[0] )

    def test_trims_pe( self ):
        for fread, rread in self.pe:
            fread_bn = basename(fread)
            rread_bn = basename(rread)
            r = self._C( (fread,rread), 40, (fread_bn,rread_bn) )
            self.check_read( fread, r[0] )
            ok_( exists( r[1] ), 'Did not produce unpaired read for {}'.format(fread_bn) )
            self.check_read( rread, r[2] )
            ok_( exists( r[3] ), 'Did not produce unpaired read for {}'.format(rread_bn) )

    def test_head_trim( self ):
        from Bio import SeqIO
        seq = 'AAAAAAAAAATTTTTTTTTTGGGGGGGGGGCCCCCCCCCC'
        qual = [1]*10 + [40]*20 + [1]*10
        sr = common.make_seqrec( seq, qual )
        c = SeqIO.write( [sr], 'single.fastq', 'fastq' )
        eq_( 1, c, 'Sanity check failed' )
        r = self._C( 'single.fastq', 10, 'single.fastq.trimmed', head_crop=10 )
        s = next( SeqIO.parse( 'single.fastq.trimmed', 'fastq' ) )
        # Should have clipped the A's and C's due to quality
        # Should have cliped the T's from the headcrop
        eq_( seq[20:30], s.seq._data )

    def test_trims_pe( self ):
        from Bio import SeqIO

        # F has 1 good read, 1 bad read
        f = 'F.fastq'
        # R has 2 good reads
        r = 'R.fastq' 
        fr = [
            common.make_seqrec( 'AAAAAAAAAA', [1]+[40]*9, id='fr1' ),
            common.make_seqrec( 'AAAAAAAAAA', [1]+[19]*9, id='fr2' ),
        ]
        rr = [
            common.make_seqrec( 'AAAAAAAAAA', [1]+[40]*9, id='rr1' ),
            common.make_seqrec( 'AAAAAAAAAA', [1]+[40]*9, id='rr2' ),
        ]
        SeqIO.write( fr, f, 'fastq' )
        SeqIO.write( rr, r, 'fastq' )

        print f
        print open(f).read()
        print r
        print open(r).read()

        # Should trim out all of fr2 due to quality
        fp = 'F.paired.fq'
        fu = fp + '.unpaired'
        rp = 'R.paired.fq'
        ru = rp + '.unpaired'
        ret = self._C( (f, r), 20, (fp,rp) )

        print fp
        print open(fp).read()
        print fu
        print open(fu).read()
        print rp
        print open(rp).read()
        print ru
        print open(ru).read()

        fseqs = list( SeqIO.parse( fp, 'fastq' ) )
        fuseqs = list( SeqIO.parse( fu, 'fastq' ) )
        rseqs = list( SeqIO.parse( rp, 'fastq' ) )
        ruseqs = list( SeqIO.parse( ru, 'fastq' ) )

        # 1 paired forward
        eq_( 1, len(fseqs) )
        # 1 paired reverse
        eq_( 1, len(rseqs) )
        # The second read was stripped because of quality
        eq_( 0, len(fuseqs) )
        # Second reverse read remains unpaired
        eq_( 1, len(ruseqs) )

        # Ensure paired end retuns correct stuff
        eq_(
            ret,
            [fp,fu,rp,ru]
        )

class TestRunCutadapt(TrimBase):
    def setUp( self ):
        super(TestRunCutadapt,self).setUp()
        self.read = self.se[0]

    def _C( self, *args, **kwargs ):
        from trim_reads import run_cutadapt
        return run_cutadapt( *args, **kwargs )

    def test_runs_correctly( self ):
        outfq = 'output.fastq'
        os.mkdir( 'trim_stats' )
        outstat = join( 'trim_stats', outfq + '.trim_stats' )
        r = self._C( self.read, stats=outstat, o=outfq, q=20 )
        # Make sure output is correct from stderr
        ll = len(r.splitlines())
        #eq_( 14, ll, 'STDERR output was not returned correctly. Got {} lines instead of 12. Output: {}'.format(ll,r) )
        ok_( exists(outstat), 'Did not create {} stats file'.format(outstat) )
        # Ensure it created the correct file name
        # Stat will freak if the file does not exist
        try:
            s = os.stat( outfq )
        except IOError as e:
            ok_( False, "Did not create correct file" )
        ok_( os.stat(self.read).st_size != s.st_size, 'No trimming happened' )

class TestRunTrimmomatic(TrimBase):
    def setUp( self ):
        super(TestRunTrimmomatic,self).setUp()
        os.mkdir( 'trim_stats' )
        self.outstat = join( 'trim_stats', 'output.trim_stats' )

    def _C( self, *args, **kwargs ):
        from trim_reads import run_trimmomatic
        return run_trimmomatic( *args, **kwargs )

    def test_runs_se_correctly( self ):
        for read in self.se:
            r = self._C( 'SE', read, 'output.fq', ('LEADING',20), trimlog=self.outstat )
            # Make sure output is correct from stderr
            ll = len(r.splitlines())
            #eq_( 14, ll, 'STDERR output was not returned correctly. Got {} lines instead of 12. Output: {}'.format(ll,r) )
            ok_( exists(self.outstat), 'Did not create {} stats file'.format(self.outstat) )
            # Ensure it created the correct file name
            ok_( exists('output.fq'), "Did not create correct file" )
            ok_( os.stat(read).st_size != os.stat('output.fq').st_size, 'No trimming happened' )

    def test_detects_quality_score_read( self ):
        # Make sure that it detects sanger and sets -phred33
        sanger = self.se[0]
        shutil.copy( sanger, 'different_name.fastq' )
        sanger = 'different_name.fastq'
        from data import NoPlatformFound
        try:
            out = self._C( 'SE', sanger, 'output.fastq', ('LEADING',20), trimlog=self.outstat )
            ok_( True )
        except NoPlatformFound as e:
            ok_( False, 'Raised NoPlatformFound when it should not have' )

    def test_runs_pe_correctly( self ):
        for fread, rread in self.pe:
            ofp = 'out.forward.paired.fq'
            ofu = 'out.forward.unpaired.fq'
            orp = 'out.reverse.paired.fq'
            oru = 'out.reverse.unpaired.fq'
            r = self._C( 'PE', fread, rread, ofp, ofu, orp, oru, ('LEADING',20), trimlog=self.outstat )

class TestIntegrate(TrimBase):
    def _C( self, *args, **kwargs ):
        script = TestIntegrate.script_path('trim_reads.py')
        return TestIntegrate.run_script( '{} {} -q {} -o {}'.format(
                script, args[0], kwargs.get('q',20), kwargs.get('o','trimmed_reads')
            )
        )

    def has_files( self, dir, efiles ):
        files = set( os.listdir( dir ) )
        efiles = set(efiles)
        print "Expected files: {}".format(efiles)
        print "Result files: {}".format(files)
        eq_( set([]), files-efiles, "{} did not contain exactly {}. Difference: {}".format(dir,efiles,files-efiles) )

    def test_runs( self ):
        outdir = 'trimmed_reads'
        r,o = self._C( self.read_dir, q=20, o=outdir )
        # Make sure exited correctly
        eq_( 0, r )
        print o
        # Make sure the file names are same as the input files
        efiles = [f.replace('.sff','.fastq') for f in os.listdir(self.read_dir)] + ['unpaired__1__TI1__2001_01_01__Unk.fastq']
        self.has_files( outdir, efiles )
        self.has_files( 'trim_stats', [f + '.trim_stats' for f in os.listdir(self.read_dir)] )
