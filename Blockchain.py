#Blockchain and Block classes
import hashlib 
import time

class Block: 
    def__init__(self, index, timestamp, data, previousHash='')
    self.index = index
    self.timestamp = timestamp
    self.data = data
    self.previousHash = previousHash #the hash of the previous block influences the current
    self.hash = self.calcHash() #hash of current block
    
    def calcHash(self) #calculates hash by calling hashlib library

class Blockchain:
    def__init__(self) 

    def createFirstBlock(self) #creating first block in chain (first transaction)
          
    def getMostRecentBlock(self) #fetching latest block in chain (latest transaction)
    
    def addBlock(self, newBlock) #adding a new block to the chain (new transaction)

    #checks if each block points to the correct previous block and if each block matches the expected calculated hash
    def isChainValid(self) 
    