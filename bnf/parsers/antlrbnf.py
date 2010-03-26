#!/usr/bin/env python

import string
import grammar

regex = '''
    (?<rule>[\w_]+)|
    (?<literal>'([^']|\\')*')|
    (?<notchars>~\([^\)]+\))|
    (?<repeat>\*\+\?)
    '''

def match(lchar,rchar,line,i,strings=True):
    depth = 1
    start = i
    i += 1
    instring = False
    while depth > 0:
        if instring:
            if line[i] == "'":
                instring = False
            elif line[i] == "\\":
                i += 1
        elif line[i] == "'":
            instring = True
        elif line[i] == lchar:
            depth += 1
        elif line[i] == rchar:
            depth -= 1
        i += 1
        if i >= len(line) and depth!=0:
            print 'failed to match %s%s: %s' % (lchar,rchar,line)
            fail
    return start, i

def match_string(i, line, char="'"):
    start = i
    i += 1
    literal = ''
    while line[i] != "'":
        if line[i] == '\\':
            literal += line[i:i+2]
            i += 2
        else:
            literal += line[i]
            i += 1
        if i >= len(line):
            print 'infinished string:',line
            fail
    return start,i+1

def linehandle(line, rule, nsubs=0):
    items = [[]]
    subs = {}
    inside = False
    i = 0
    while i<len(line):
        char = line[i]
        if char in ' \t':
            i += 1
        elif char in '~*?+':
            items[-1].append(char)
            i += 1
        elif char == '.':
            if line[i+1]=='.':
                items[-1].append('..')
                i += 2
            else:
                items[-1].append(char)
                i += 1
        elif char == "'":
            literal = '!'
            start, i = match_string(i, line)
            literal += line[start+1:i-1]
            items[-1].append(literal)
            i += 1
        elif char == '(':
            start, i = match('(',')',line,i,True)

            sitems, ssubs, nsubs = linehandle(line[start+1:i-1], rule, nsubs)
            subs.update(ssubs)
            subs[rule + '-%d' % nsubs] = sitems
            items[-1].append('@' + rule + '-%d' % nsubs)
            nsubs += 1

        elif char == '|':
            items.append([])
            i += 1

        elif char in string.ascii_letters:
            rulename = '@'
            while i<len(line) and line[i] in string.ascii_letters+string.digits+'_':
                rulename += line[i]
                i += 1
            items[-1].append(rulename)

        elif char == '{':
            start, i = match('{','}',line,i,True)
            print 'skipping:',line[start:i]

        elif char == '=' and line[i+1] == '>':
            print 'idk'
            break

        elif char == '/' and line[i+1] == '/':
            break

        else:
            print 'weird char found: %s; %d; %s' % (line[i],i,line)
            fail
    return items, subs, nsubs

def split(text):
    rules = {}
    num_lines = {}
    order = []
    name = None
    startat = -1
    items = []
    lines = []
    inrule = False
    for i,line in enumerate(text.split('\n')):
        line = line.strip()
        if line.strip().startswith('//') or not line.strip():
            continue
        if inrule == 2 and line.strip() == ';':
            num_lines[name] = [startat, lines]
            items, rsubs, nsubs = linehandle(lines, name)
            rules[name] = items
            rules.update(rsubs)
            for sname in rsubs:
                num_lines[sname] = [startat, lines]
            items = []
            lines = ''
            inrule = 0
        elif not inrule:
            name = line.split(' ')[0]
            if name == 'fragment':
                continue
            inrule = 1
            if line.split(' ',1)[-1].startswith(':'):
                if line.endswith(';'):
                    lines = line.split(':',1)[1][:-1]
                    num_lines[name] = [startat, lines]
                    items, rsubs, nsubs = linehandle(lines, name)
                    rules[name] = items
                    rules.update(rsubs)
                    for sname in rsubs:
                        num_lines[sname] = [startat, lines]
                    items = []
                    lines = ''
                    inrule = 0
            else:
                order.append(name)
                startat = i
        elif inrule == 1 and line.strip().startswith(':'):
            inrule = 2
            lines = line.strip()[1:]
        elif inrule == 2:# and line.strip().startswith('|'):
            if '//' in line:
                line = line.split('//')[0]
            lines += line.strip()
    return rules, order, num_lines

class Grammar(grammar.Grammar):
    def loadrules(self):
        rules,order,lines = split(self.original)
        self.rules = rules
        self.order = order
        self.lines = lines
        print rules['HEX_LITERAL']
        #print rules
        print len(rules)

# vim: et sw=4 sts=4