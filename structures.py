#!/usr/bin/env python

class Document:
	def __init__(self, guid, owner, title, content, postdate, embeds):
		self.guid=guid
		self.owner=owner
		self.title=title
		self.content=content
		self.postdate=postdate
		self.embeds=embeds
	def __repr__(self):
		return self.guid
	def getTitle(self):
		return self.title
	def createClip(self, start, length):
		return Clip("_".join(["C", self.guid, str(start), str(length)]), self, start, length)
	def createEmbed(self, doc, start, length, pos):
		ret=Embed("_".join(["E", self.guid, str(pos), doc.guid, str(start), str(length)]), doc.createClip(start, length), self, pos)
		if(doc in self.embeds):
			self.embeds[doc].append(ret)
		else:
			self.embeds[doc]=[ret]
		return ret
	def getSpan(self, start, length):
		if(start+length>len(self.content)):
			length=len(self.content)-start
		return self.content[start:start+length]
	def getEmbedsByPos(self):
		embedsByPos={}
		for doc in self.embeds:
			for item in self.embeds[doc]:
				pos=item.getPos()
				if not (pos in embedsByPos):
					embedsByPos[pos]=[item]
				else:
					embedsByPos[pos].append[item]
		return embedsByPos
	def getEmbeds(self, start=0, end=-1):
		embedsSorted=[]
		embedsByPos=self.getEmbedsByPos()
		keys=embedsByPos.keys()
		keys.sort()
		for key in keys:
			if(key>=start):
				if(end<0 or key<end):
					embedsSorted.extend(embedsByPos[key])
		return embedsSorted
	def getSection(self, start, length, user):
		# Get $length billed characters starting at $start
		end=start+length
		embedsByPos=self.getEmbedsByPos()
		embedPositions=embedsByPos.keys()
		embedPositions.sort()
		chunks=[]
		lastI=0
		for i in embedPositions:
			if(i<len(self.content)):
				if(i!=lastI):
					chunks.append(self.content[lastI:i])
					lastI=i
		if(lastI<len(self.content)):
			chunks.append(self.content[lastI:])
		done=False
		ret=[]
		ax=0
		i=0
		chunk=0
		while(i<len(self.content) and ax<end and not done):
			if(i in embedPositions):
				for item in embedsByPos[i]:
					if(ax>=start and ax<=end):
						if(ax+item.getLength()<=end):
							item.purchase(user)
							ret.append(item)
							ax+=item.getLength()
						else:
							ret.append(item.subEmbed(0, (ax+item.getLength())-end))
							ax+=ret[-1].getLength()
							ret[-1].purchase(user)
					elif(ax+item.getLength()>start and ax<start):
						delta=start-ax
						if(ax+item.getLength()<=end):
							ret.append(item.subEmbed(delta, item.getLength()-delta))
							ax+=ret[-1].getLength()
							ret[-1].purchase(user)
						else:
							delta2=delta-length
							ret.append(item.subEmbed(delta, delta2))
							ax+=ret[-1].getLength()
							ret[-1].purchase(user)
			if(chunk<len(chunks)):
				cL=len(chunks[chunk])
				if(ax>=start and ax<=end):
					if(ax+cL<=end):
						ret.append(chunks[chunk])
						user.purchaseSpan(self, i, cL)
						ax+=cL
						i+=cL
					else:
						delta=(ax+cL)-end
						ret.append(chunks[chunk][:delta])
						user.purchaseSpan(self, i, cL-delta)
						ax+=delta
						i+=delta
				elif(ax+cL>start and ax<start):
					delta=start-ax
					if(ax+cL<=end):
						ret.append(chunks[chunk][delta:])
						user.purchaseSpan(self, i+delta, len(ret[-1]))
						ax+=len(ret[-1])
						i+=len(ret[-1])
					else:
						delta2=delta-length
						ret.append(chunks[chunk][delta:delta2])
						user.purchaseSpan(self, i+delta, len(ret[-1]))
						ax+=len(ret[-1])
						i+=len(ret[-1])
			else:
				if(i>embedPositions[-1]):
					done=True
			chunk+=1
		return ret
	def getFormattedSection(self, start, length, user):
		formattedSection=["<h1>"+self.title+"</h1>"]
		section=self.getSection(start, length, user)
		for chunk in section:
			if(type(chunk)==str):
				formattedSection.append(chunk)
			else:
				clip=chunk.clip
				oDoc=clip.doc
				title="<a href=\""+oDoc.guid+"\">"+oDoc.title+"</a>"
				tmp="<p/ ><blockquote><table><th><td>"+title+"</td></th><tr><td>"
				tmp+=chunk.getContent()+"</td></th></blockquote>"
				formattedSection.append(tmp)
		return "<p />".join(formattedSection).replace("\n", "<p />")
class Clip:
	def __init__(self, guid, doc, start, length):
		self.guid=guid
		self.doc=doc
		self.start=start
		self.length=length
	def __repr__(self):
		return self.guid
	def getTitle(self):
		return self.doc.getTitle()
	def getContent(self):
		return self.doc.getSpan(self.start, self.length)
	def subClip(self, start, length):
		return Clip("_".join([self.guid, str(self.start+start), str(length)]), self.doc, self.start+start, length)
	def purchase(self, user):
		return user.purchaseSpan(self.doc, self.start, self.length)

class Embed:
	def __init__(self, guid, clip, doc, pos):
		self.guid=guid
		self.clip=clip
		self.doc=doc
		self.pos=pos
	def __repr__(self):
		return self.guid
	def getTitle(self):
		return self.clip.getTitle()
	def getContent(self):
		return self.clip.getContent()
	def getPos(self):
		return self.pos
	def getLength(self):
		return self.clip.length
	def subEmbed(self, start, length):
		return Embed("_".join([self.guid, str(self.start+start), str(length)]), self.clip.subClip(start, length), self.doc, self.pos)
	def purchase(self, user):
		return self.clip.purchase(user)

class User:
	def __init__(self, guid, name, balance, owns):
		self.guid=guid
		self.name=name
		self.balance=balance
		self.owns=owns
	def __repr__(self):
		return self.guid
	def createDoc(self, title, content, postdate, embeds):
		return Document(self.guid+str(postdate), self, title, content, postdate, embeds)
	def purchaseSpan(self, document, start, length):
		if(document.owner.guid==self.guid):
			return True
		if(document in self.owns):
			end=start+length
			for span in self.owns[document]:
				iEnd=span[0]+span[1]
				if(span[0]==start and span[1]==length):
					return True # already purchased
				elif(span[0]<=start):
					if(iEnd>start):
						if(iEnd<end):
							# We own part of what we need, and we just need the tail end
							newLength=end-iEnd
							self.balance-=newLength
							document.owner.balance+=newLength
							self.owns[document].append([iEnd, newLength])
						else:
							# The span we are requesting is within a span we already own
							return True
					else:
						pass # This span doesn't intersect
				elif(iEnd<end):
					# We own the tail end of what we need, and need the beginning
					newLength=span[0]-start
					self.balance-=newLength
					document.owner.balance+=newLength
					self.owns[document].append([start, newLength])
					return True
		else:
			self.owns[document]=[]
					
		self.balance-=length
		document.owner.balance+=length
		self.owns[document].append([start, length])
		return True

def test():
	alice=User("alice", "Alice", 0, {})
	bob=User("bob", "Bob", 1000, {})
	plusses=alice.createDoc("Plusses", "+"*500, 0, {})
	minuses=alice.createDoc("Minuses", "-"*500, 1, {})
	print(alice)
	print(alice.balance)
	print(alice.owns)
	print(bob)
	print(bob.balance)
	print(bob.owns)
	print(plusses)
	print(minuses)
	minuses.createEmbed(plusses, 0, 500, 250)
	print(minuses.getFormattedSection(0, 1000, bob))
	print(alice.balance)
	print(bob.balance)
test()
